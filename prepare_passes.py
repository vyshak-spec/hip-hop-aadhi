"""Convert the 5 designer ticket files (print CMYK, ~5 MB each) into web-ready sRGB passes."""
import io
import os

from PIL import Image, ImageCms

# (slug, pass name, price, original ticket file, badge colours)
# The slug is printed inside the QR code - never change it once the codes are out.
TIERS = [
    ("mip-elite-pass", "MIP Elite Pass", "25,000", "MIP elite ticket.jpg.jpeg", ("#c4122f", "#f2b632")),
    ("vvip-pass", "VVIP Pass", "10,000", "VVIP Ticket.jpg.jpeg", ("#0f7a3c", "#e3b53b")),
    ("fanpit-pass", "Fanpit Pass", "2,499", "Fanpit Ticket.jpg.jpeg", ("#d1491b", "#f2a23a")),
    ("gold-pass", "Gold Pass", "1,099", "Gold Ticket.jpg.jpeg", ("#b8860b", "#f5d061")),
    ("silver-pass", "Silver Pass", "599", "Silver ticket.jpg.jpeg", ("#1c4fd8", "#9fb3c8")),
]

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
    os.makedirs(PASS_DIR, exist_ok=True)
    for slug, name, price, source, _ in TIERS:
        img = to_srgb(Image.open(source))
        img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
        out = f"{PASS_DIR}/{slug}.jpg"
        img.save(out, quality=86, optimize=True, progressive=True)
        print(f"{name} (Rs {price}): {source} -> {out} {img.size} {os.path.getsize(out) // 1024} KB")
