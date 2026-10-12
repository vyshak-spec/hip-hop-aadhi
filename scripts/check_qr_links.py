"""Fail if any printed QR code link would break, or any QR image has changed.

The 5 paths below are printed on QR codes and must never change. This list is kept
separate from make_qr.py on purpose, so a change to the generator can't silently
change what is protected. QR_LOCK freezes each QR image itself: if a file in qr/ is
redrawn, its fingerprint changes and this check fails.

Usage:
  python scripts/check_qr_links.py                                  # check docs/ and qr/ files
  python scripts/check_qr_links.py --live https://events.iqtechmax.com  # check the live site
"""
import hashlib
import os
import sys
import urllib.request

QR_PATHS = [
    "star-galatta/mip-elite-pass",
    "star-galatta/vvip-pass",
    "star-galatta/fanpit-pass",
    "star-galatta/gold-pass",
    "star-galatta/silver-pass",
]

# SHA-256 of each frozen QR image (each encodes https://events.iqtechmax.com/<path>).
QR_LOCK = {
    "qr_mip-elite-pass.png": "b94d80dc92a165f02b840919de08c097f6e522b538bd29dfba123cd3243b3e59",
    "qr_vvip-pass.png": "a4756f57afcb90b0eacb0ff6f2f0147b5b570c0404d09556ceda86d0428a7d3a",
    "qr_fanpit-pass.png": "ba319357bd1c3d13fcdf918711da458b8fbacf2812e1e75d99ffd94605c30b17",
    "qr_gold-pass.png": "8964978c7aa3ae4976ea78a24ea337e4dc4ca6515caa26cd7cd7bb2ba58103ad",
    "qr_silver-pass.png": "2b68fd09c15adecf0cba4afd2b4e102466de32d29871d15e5018c1ef95feadcd",
}

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOCS = os.path.join(ROOT, "docs")
QR_DIR = os.path.join(ROOT, "qr")


def check_files():
    missing = [p for p in QR_PATHS
               if not os.path.isfile(os.path.join(DOCS, p, "index.html"))]
    for p in missing:
        print(f"MISSING  docs/{p}/index.html")
    return missing


def check_qr_images():
    changed = []
    for name, digest in QR_LOCK.items():
        path = os.path.join(QR_DIR, name)
        if not os.path.isfile(path):
            changed.append(name)
            print(f"MISSING  qr/{name}")
        elif hashlib.sha256(open(path, "rb").read()).hexdigest() != digest:
            changed.append(name)
            print(f"CHANGED  qr/{name}  (restore it: git checkout -- qr/{name})")
    return changed


def check_live(base):
    broken = []
    for p in QR_PATHS:
        url = f"{base.rstrip('/')}/{p}"
        try:
            status = urllib.request.urlopen(url, timeout=20).status
        except Exception as e:  # HTTPError, timeouts, DNS failures
            status = e
        if status != 200:
            broken.append(url)
            print(f"BROKEN   {url}  ({status})")
    return broken


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--live":
        problems = check_live(sys.argv[2])
        if problems:
            sys.exit(f"{len(problems)} of {len(QR_PATHS)} printed QR links are broken on the live site.")
        print(f"All {len(QR_PATHS)} printed QR links OK on the live site.")
    else:
        missing, changed = check_files(), check_qr_images()
        if missing:
            print(f"{len(missing)} of {len(QR_PATHS)} printed QR links are broken in docs/.")
        if changed:
            print(f"{len(changed)} of {len(QR_LOCK)} frozen QR images are missing or changed in qr/.")
        if missing or changed:
            sys.exit(1)
        print(f"All {len(QR_PATHS)} printed QR links OK in docs/, all {len(QR_LOCK)} QR images unchanged.")
