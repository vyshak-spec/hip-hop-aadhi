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
    "hiphop-aadhi/mip-elite-pass",
    "hiphop-aadhi/vvip-pass",
    "hiphop-aadhi/fanpit-pass",
    "hiphop-aadhi/gold-pass",
    "hiphop-aadhi/silver-pass",
]

# SHA-256 of each frozen QR image (each encodes https://events.iqtechmax.com/<path>).
QR_LOCK = {
    "qr_mip-elite-pass.png": "4d228c64d005bff2355ceb73835d62ed5a78ac321fc58c2c5b25c75e23fdf3ea",
    "qr_vvip-pass.png": "5ca892d2c28a068c0a73e999377e75c93c1660e372c41be5b8a0ff3b87dd9577",
    "qr_fanpit-pass.png": "fcb53f5e49ef4cc71141db96a59179da53bf3708817ca069d092aea09f564d5d",
    "qr_gold-pass.png": "4826caccabdec9ef0859aec1f60091b4d87658684b406429ee743bcd8c386d03",
    "qr_silver-pass.png": "3a806b4bf2031578ee9b8c0606310bb5a1ffaff882372c162dbd2d3109e3e4af",
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
