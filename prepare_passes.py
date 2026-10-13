"""Convert the 5 designer ticket files (print CMYK, ~5 MB each) into web-ready sRGB passes."""
import io
import os

from PIL import Image, ImageCms

# (slug, pass name, price, original ticket file, badge colours)
# The slug is inside the printed QR code - never change it. The name and price can change freely:
# the client renamed Fanpit -> Gold, Gold -> Silver, Silver -> Bronze, so those slugs keep the old names.
TIERS = [
    ("mip-elite-pass", "MIP Elite Pass", "25,000", "MIP elite ticket.jpg.jpeg", ("#c4122f", "#f2b632")),
    ("vvip-pass", "VVIP Pass", "10,000", "VVIP Ticket.jpg.jpeg", ("#0f7a3c", "#e3b53b")),
    ("fanpit-pass", "Gold Pass", "2,499", "Fanpit Ticket.jpg.jpeg", ("#b8860b", "#f5d061")),
    ("gold-pass", "Silver Pass", "1,099", "Gold Ticket.jpg.jpeg", ("#5f6b78", "#c9d3dd")),
    ("silver-pass", "Bronze Pass", "599", "Silver ticket.jpg.jpeg", ("#7a3e17", "#cd7f32")),
]

# The name the designer's artwork prints on the side strip, and its ink. Where it differs from the
# pass name above, relabel.py replaces it on the picture (prices on the artwork are already right).
PRINTED = {
    "fanpit-pass": ("FANPIT PASS", "gold"),
    "gold-pass": ("GOLD PASS", "gold"),
    "silver-pass": ("SILVER PASS", "silver"),
}

PASS_DIR = "passes"
WIDTH = 2200  # wide enough to zoom into the small print on a phone


def to_srgb(img):
    """Use the file's own colour profile; a plain convert() shifts CMYK colours."""
    icc = img.info.get("icc_profile")
    if img.mode == "CMYK" and icc:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return ImageCms.profileToProfile(img, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
    return img.convert("RGB")


if __name__ == "__main__":
    from relabel import relabel  # needs opencv and fonttools; only this build step uses it

    os.makedirs(PASS_DIR, exist_ok=True)
    for slug, name, price, source, _ in TIERS:
        img = to_srgb(Image.open(source))
        printed, ink = PRINTED.get(slug, (name.upper(), None))
        if printed != name.upper():
            img = relabel(img, printed, name.upper(), ink)
            print(f"  artwork name {printed} -> {name.upper()}")
        img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
        out = f"{PASS_DIR}/{slug}.jpg"
        img.save(out, quality=86, optimize=True, progressive=True)
        print(f"{name} (Rs {price}): {source} -> {out} {img.size} {os.path.getsize(out) // 1024} KB")
