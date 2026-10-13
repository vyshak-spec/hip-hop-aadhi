"""Build the 5 booking-pass pages and their QR code images."""
import os
import shutil

import qrcode
from PIL import Image, ImageDraw, ImageFont

from prepare_passes import PASS_DIR, TIERS

# FROZEN: this link is inside the printed QR codes. Never change it.
BASE_URL = "https://events.iqtechmax.com/star-galatta/"
SITE = "docs"
EVENT_DIR = f"{SITE}/star-galatta"
QR_DIR = "qr"
CODE_DIR = f"{QR_DIR}/code"  # the frozen QR patterns, without the label
FONT = "C:/Windows/Fonts/arialbd.ttf"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{name} | Star Galatta Salem 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center;
         justify-content: center; gap: 20px; padding: 16px; background: radial-gradient(circle at 50% 0%, {c1}55 0%, #0b0b0f 62%);
         color: #f7f2ea; font-family: "Outfit", system-ui, sans-serif; }}
  figure {{ margin: 0; width: min(100%, 960px); border-radius: 18px; overflow: hidden;
           background: #111015; box-shadow: 0 24px 60px rgba(0, 0, 0, .6); }}
  .pass a {{ display: block; }}
  .pass img {{ display: block; width: 100%; height: auto; }}
  .hint {{ margin: 0; font-size: 12px; font-weight: 300; color: #8d8579; }}
  .details {{ padding: 22px; }}
  .tier {{ display: inline-block; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
          letter-spacing: .18em; background: linear-gradient(90deg, {c1}, {c2}); color: #fff;
          text-shadow: 0 1px 2px rgba(0, 0, 0, .35); }}
  h1 {{ margin: 12px 0 6px; font-size: clamp(26px, 7vw, 38px); font-weight: 800; line-height: 1.05;
       letter-spacing: -.02em; }}
  .info {{ margin: 0; font-size: 15px; font-weight: 300; color: #d8cfc2; }}
  .foot {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px;
          margin-top: 16px; }}
  .brand {{ margin: 0; font-size: 12px; font-weight: 400; letter-spacing: .14em; text-transform: uppercase;
           color: #8d8579; }}
  .powered {{ display: flex; align-items: center; gap: 8px; opacity: .85; }}
  .powered span {{ font-size: 8px; font-weight: 600; letter-spacing: .24em; color: #fff; }}
  .powered img {{ display: block; width: 96px; height: auto; }}
</style>
</head>
<body>
<figure class="pass">
  <a href="../img/{slug}.jpg"><img src="../img/{slug}.jpg" alt="Star Galatta Salem 2026 - {name}, Rs {price}"></a>
</figure>
<p class="hint">Tap the pass to open it full size</p>
<figure>
  <div class="details">
    <span class="tier">{name_upper} &middot; &#8377;{price}</span>
    <h1>Star Galatta Salem 2026</h1>
    <p class="info">Sat, Oct 31 &middot; 5 &ndash; 10 PM &middot; Vysya College, Salem</p>
    <div class="foot">
      <p class="brand">Hiphop Aadhi &middot; Live in Concert</p>
      <div class="powered"><span>POWERED BY</span><img src="../img/iqtechmax_white.png" alt="IQ Techmax"></div>
    </div>
  </div>
</figure>
</body>
</html>
"""


def build_watermark(out):
    """White, transparent, side-by-side version of iqtechmax_logo.png (icon left of the wordmark)."""
    logo = Image.open("iqtechmax_logo.png").convert("L")
    icon, word = logo.crop((98, 134, 235, 382)), logo.crop((44, 413, 301, 459))
    icon = icon.resize((round(icon.width * 96 / icon.height), 96), Image.LANCZOS)
    gap = 18
    shade = Image.new("L", (icon.width + gap + word.width, icon.height), 255)
    shade.paste(icon, (0, 0))
    shade.paste(word, (icon.width + gap, (icon.height - word.height) // 2))
    # dark ink -> opaque white, white paper -> transparent
    alpha = shade.point(lambda v: min(255, round((255 - v) * 1.25)))
    mark = Image.new("RGBA", shade.size, (255, 255, 255, 0))
    mark.putalpha(alpha)
    mark.save(out)


def build_site():
    shutil.rmtree(SITE, ignore_errors=True)
    os.makedirs(f"{EVENT_DIR}/img")
    build_watermark(f"{EVENT_DIR}/img/iqtechmax_white.png")
    for slug, name, price, _, (c1, c2) in TIERS:
        shutil.copy(f"{PASS_DIR}/{slug}.jpg", f"{EVENT_DIR}/img/{slug}.jpg")
        # A folder with index.html, so any web server answers the extension-less URL.
        os.makedirs(f"{EVENT_DIR}/{slug}")
        with open(f"{EVENT_DIR}/{slug}/index.html", "w", encoding="utf-8") as f:
            f.write(PAGE.format(slug=slug, name=name, name_upper=name.upper(), price=price, c1=c1, c2=c2))
    # GitHub Pages copy: serve folders as-is (no Jekyll processing).
    open(f"{SITE}/.nojekyll", "w").close()


def build_qr():
    os.makedirs(CODE_DIR, exist_ok=True)
    big, small = ImageFont.truetype(FONT, 44), ImageFont.truetype(FONT, 30)
    for slug, name, price, _, _ in TIERS:
        out = f"{QR_DIR}/qr_{slug}.png"
        pattern = f"{CODE_DIR}/{slug}.png"
        # The QR patterns are frozen: an existing one is reused as-is, never redrawn
        # (see scripts/check_qr_links.py). Only the label under it is drawn fresh.
        if os.path.exists(pattern):
            code = Image.open(pattern).convert("RGB")
        else:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=4)
            qr.add_data(BASE_URL + slug)
            code = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            code.save(pattern)
            print(f"{pattern} NEW pattern -> {BASE_URL + slug}")

        card = Image.new("RGB", (code.width, code.height + 130), "white")
        card.paste(code, (0, 0))
        draw = ImageDraw.Draw(card)
        cx = code.width // 2
        draw.text((cx, code.height + 10), f"{name.upper()}  |  RS {price}", font=big, fill="black", anchor="mt")
        draw.text((cx, code.height + 70), "Star Galatta  ·  Salem 2026", font=small, fill="#444444", anchor="mt")
        card.save(out)
        print(f"{out} ({name}, Rs {price}) -> {BASE_URL + slug}")


if __name__ == "__main__":
    if not BASE_URL:
        raise SystemExit("Set BASE_URL in make_qr.py first.")
    build_site()
    build_qr()
