"""Replace the pass name printed on a ticket's side strip, keeping the strip's background and finish.

The artwork prints the pass name rotated on the left strip, in Bebas Neue with a gold or silver
gradient. relabel() erases that name, rebuilds the background behind it (smooth colour plus the
strip's own texture), and draws the new name in the same font, size, spacing and gradient.
Size and spacing are fitted by redrawing the old name over the original first, so each ticket
calibrates itself. The price line and the rest of the artwork are not touched.
"""
import numpy as np
import cv2
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FONT = "fonts/BebasNeue-Regular.ttf"
STRIP = 480      # width of the side strip in the 2750 x 1000 artwork
LEFT, RIGHT = 45, 955  # the name stays inside this span of the upright strip (clear of the frame)
SS = 4           # supersampling for smooth letter edges


def ink_mask(a, ink):
    """Pixels of the printed text (and the frame, which uses the same ink)."""
    a = a.astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (r * 299 + g * 587 + b * 114) // 1000
    if ink == "silver":  # white/grey text on blue
        return (lum > 150) & (b - r < 60)
    return (lum > 120) & (r > b + 40)  # gold text on brown or black


def smooth_fill(values, weight, sigmas):
    """Spread values from weighted pixels to their surroundings (normalised blur)."""
    out = np.zeros_like(values)
    done = np.zeros(weight.shape, bool)
    for s in sigmas:
        w = cv2.GaussianBlur(weight, (0, 0), s)
        v = cv2.GaussianBlur(values * weight[..., None], (0, 0), s)
        ok = (w > 1e-3) & ~done
        out[ok] = v[ok] / w[ok][:, None]
        done |= ok
    out[~done] = (values * weight[..., None]).sum((0, 1)) / max(weight.sum(), 1)
    return out


class Font:
    def __init__(self):
        self.tt = TTFont(FONT)
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.cap = self.tt["OS/2"].sCapHeight
        self.lookups = [l for l in self.tt["GPOS"].table.LookupList.Lookup if l.LookupType == 2]

    def advance(self, ch):
        return self.tt["hmtx"][self.cmap[ord(ch)]][0]

    def kern(self, left, right):
        """Pair kerning in font units, from the font's GPOS table."""
        gl, gr = self.cmap[ord(left)], self.cmap[ord(right)]
        total = 0
        for lookup in self.lookups:
            for st in lookup.SubTable:
                if gl not in st.Coverage.glyphs:
                    continue
                if st.Format == 1:
                    pairs = st.PairSet[st.Coverage.glyphs.index(gl)].PairValueRecord
                    rec = next((p for p in pairs if p.SecondGlyph == gr), None)
                    if rec is None:
                        continue
                    total += getattr(rec.Value1, "XAdvance", 0) or 0
                else:
                    c1 = st.ClassDef1.classDefs.get(gl, 0)
                    c2 = st.ClassDef2.classDefs.get(gr, 0)
                    total += getattr(st.Class1Record[c1].Class2Record[c2].Value1, "XAdvance", 0) or 0
                break  # the first matching subtable of a lookup applies
        return total

    def render(self, text, cap_px, track, bold, scale=1):
        """Coverage mask (0..1) of text whose capitals are cap_px tall, cropped to the ink."""
        size = cap_px * self.upm / self.cap * scale
        pil = ImageFont.truetype(FONT, round(size))
        k = size / self.upm
        pen, xs = 0.0, []
        for i, ch in enumerate(text):
            xs.append(pen)
            pen += self.advance(ch) * k + track * scale
            if i + 1 < len(text):
                pen += self.kern(ch, text[i + 1]) * k
        img = Image.new("L", (int(pen + size), int(size * 1.6)), 0)
        draw = ImageDraw.Draw(img)
        for x, ch in zip(xs, text):
            draw.text((x + size * 0.1, size * 1.2), ch, font=pil, fill=255, anchor="ls")
        m = np.asarray(img, np.float32) / 255
        if bold:
            m = cv2.dilate(m, np.ones((2 * bold * scale + 1,) * 2, np.uint8))
        ys, xs_ = np.where(m > 0.5)
        return m[ys.min():ys.max() + 1, xs_.min():xs_.max() + 1]


def name_glyphs(strip, ink):
    """Mask and box of the big name letters in an upright strip (price line and frame excluded)."""
    ink_px = ink_mask(strip, ink).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink_px, 8)
    big = [i for i in range(1, n) if 150 <= st[i, 3] <= 200 and st[i, 2] < 150]
    top = np.median([st[i, 1] for i in big])
    big = [i for i in big if abs(st[i, 1] - top) <= 12]
    mask = np.isin(lab, big)
    x0 = min(st[i, 0] for i in big)
    x1 = max(st[i, 0] + st[i, 2] for i in big)
    y0 = min(st[i, 1] for i in big)
    y1 = max(st[i, 1] + st[i, 3] for i in big)
    return mask, (x0, y0, x1, y1), ink_px.astype(bool)


def copy_texture(texture, valid, erase, seed=7):
    """Fill the erased pixels with the strip's fine texture, copied in patches from clean background.

    Each target patch takes one randomly chosen patch of clean background (fixed seed, so rebuilds
    give the same picture); patches shrink only where no clean patch of that size exists.
    """
    rng = np.random.default_rng(seed)
    out = np.zeros_like(texture)
    todo = erase.copy()
    h, w = valid.shape
    integral = cv2.integral(valid.astype(np.uint8))
    for size in (32, 16, 8, 4, 1):
        n = size * size
        all_valid = (integral[size:, size:] - integral[:-size, size:]
                     - integral[size:, :-size] + integral[:-size, :-size]) == n
        sy, sx = np.nonzero(all_valid[::2, ::2])
        if not len(sy):
            continue
        sy, sx = sy * 2, sx * 2
        for ty in range(0, h, size):
            for tx in range(0, w, size):
                need = todo[ty:ty + size, tx:tx + size]
                if not need.any():
                    continue
                k = rng.integers(len(sy))
                th, tw = need.shape
                src = texture[sy[k]:sy[k] + th, sx[k]:sx[k] + tw]
                out[ty:ty + th, tx:tx + tw][need] = src[need]
                todo[ty:ty + th, tx:tx + tw] = False
    return out


def iou(a, b):
    return (a & b).sum() / max((a | b).sum(), 1)


def place(canvas_shape, m, x, y):
    out = np.zeros(canvas_shape, np.float32)
    h, w = m.shape
    out[y:y + h, x:x + w] = m[:canvas_shape[0] - y, :canvas_shape[1] - x]
    return out


def fit(font, old_text, mask, box):
    """Find cap height, tracking and weight that redraw old_text over the original best."""
    x0, y0, x1, y1 = box
    best = None
    for cap in range(170, 181):
        for track in range(-6, 7):
            for bold in (0, 1):
                m = font.render(old_text, cap, track, bold) > 0.5
                drawn = place(mask.shape, m, x0, y0) > 0.5
                score = iou(drawn, mask)
                if not best or score > best[0]:
                    best = (score, cap, track, bold)
    return best


def relabel(img, old_text, new_text, ink, report=None):
    """Return img (2750 x 1000 RGB) with the strip's printed name changed from old_text to new_text."""
    font = Font()
    a = np.asarray(img).copy()
    strip = np.rot90(a[:, :STRIP], k=-1).copy()  # the name reads left to right
    mask, box, ink_px = name_glyphs(strip, ink)
    score, cap, track, bold = fit(font, old_text, mask, box)
    f = strip.astype(np.float32)

    # 1. colour of the letters at each spot (the gradient), from the old letters' inner pixels
    core = cv2.erode(mask.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
    ink_colour = smooth_fill(f, core, (10, 40, 150))

    # 2. background without the old name: smooth colour + the strip's own fine texture
    erase = cv2.dilate(mask.astype(np.uint8), np.ones((11, 11), np.uint8)).astype(bool)
    lum = f.mean(2)
    valid = ~cv2.dilate(ink_px.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & (lum < 200)
    valid[:35] = valid[-10:] = False
    valid[:, :30] = valid[:, -30:] = False
    base = smooth_fill(f, valid.astype(np.float32), (18, 60, 200))
    texture = f - cv2.GaussianBlur(f, (0, 0), 2.5)
    clean = base + copy_texture(texture, valid, erase)
    soft = cv2.GaussianBlur(cv2.dilate(erase.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32),
                            (0, 0), 1.5)[..., None]
    soft = np.maximum(soft, erase[..., None])
    bg = f * (1 - soft) + clean * soft

    # 3. the new name: same cap height, spacing and weight, centred where the old name was
    m = font.render(new_text, cap, track, bold, scale=SS)
    if m.shape[1] / SS > RIGHT - LEFT:  # too long for the panel: shrink to fit
        cap = cap * (RIGHT - LEFT) * SS / m.shape[1]
        m = font.render(new_text, cap, track, bold, scale=SS)
    m = cv2.resize(m, (round(m.shape[1] / SS), round(m.shape[0] / SS)), interpolation=cv2.INTER_AREA)
    centre = (box[0] + box[2]) / 2
    nx = min(max(round(centre - m.shape[1] / 2), LEFT), RIGHT - m.shape[1])
    ny = box[1] + (box[3] - box[1] - m.shape[0]) // 2  # same middle line (matters if shrunk)
    alpha = place(mask.shape, m, nx, ny)[..., None]
    out = bg * (1 - alpha) + ink_colour * alpha

    a[:, :STRIP] = np.rot90(np.clip(out + 0.5, 0, 255).astype(np.uint8), k=1)
    if report is not None:
        report.update(fit_iou=round(float(score), 3), cap=round(float(cap), 1), track=track, bold=bold,
                      old_box=box, new_box=(nx, ny, nx + m.shape[1], ny + m.shape[0]))
    return Image.fromarray(a)
