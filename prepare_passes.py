"""Convert the designer's ticket files (front and back of each pass, ~3 MB each) into web-ready sRGB passes."""
import io
import os

from PIL import Image, ImageCms

# (slug, pass name, price, (front, back) ticket files in passes/, badge colours)
# The slug is inside the QR code - never change it once the codes are shared. The name and price
# can change freely.
TIERS = [
    ("mip-elite-pass", "MIP Elite Pass", "25,000", ("MIP front.jpg.jpeg", "MIP back.jpg.jpeg"),
     ("#c4122f", "#f2b632")),
    ("vvip-pass", "VVIP Pass", "10,000", ("VVIP Front.jpg.jpeg", "VVIP back.jpg.jpeg"),
     ("#0f7a3c", "#e3b53b")),
    ("gold-pass", "Gold Pass", "2,499", ("Gold front.jpg.jpeg", "Gold back.jpg.jpeg"),
     ("#b8860b", "#f5d061")),
    ("silver-pass", "Silver Pass", "1,099", ("Silver Front.jpg.jpeg", "Silver back.jpg.jpeg"),
     ("#5f6b78", "#c9d3dd")),
    ("bronze-pass", "Bronze Pass", "599", ("Bronze Ticket.jpg.jpeg", "Bronze back.jpg.jpeg"),
     ("#7a3e17", "#cd7f32")),
]
SIDES = ("", "-back")  # passes/<slug>.jpg is the front, passes/<slug>-back.jpg the back

# The name the designer's artwork prints on the side strip, and its ink, where it differs from the
# pass name above; relabel.py then replaces it on the picture. The Oct 14 artwork prints the
# right names on all 5 passes, so nothing is replaced.
PRINTED = {}

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
    for slug, name, price, sources, _ in TIERS:
        for source, side in zip(sources, SIDES):
            img = to_srgb(Image.open(f"{PASS_DIR}/{source}"))
            printed, ink = PRINTED.get(slug, (name.upper(), None))
            if printed != name.upper():
                img = relabel(img, printed, name.upper(), ink)
                print(f"  artwork name {printed} -> {name.upper()}")
            img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
            out = f"{PASS_DIR}/{slug}{side}.jpg"
            img.save(out, quality=86, optimize=True, progressive=True)
            print(f"{name} (Rs {price}): {source} -> {out} {img.size} {os.path.getsize(out) // 1024} KB")
