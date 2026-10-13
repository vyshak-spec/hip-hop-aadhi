"""Fail if any printed QR code link would break, or any QR image has changed.

The 5 paths below are printed on QR codes and must never change. This list is kept
separate from make_qr.py on purpose, so a change to the generator can't silently
change what is protected. QR_LOCK freezes each QR pattern itself (qr/code/, the code
without its label): if one is redrawn, its fingerprint changes and this check fails.
The label under the code (pass name, price) is not locked, so it can be updated.

Usage:
  python scripts/check_qr_links.py                                  # check docs/ and qr/code/ files
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

# SHA-256 of each frozen QR pattern (each encodes https://events.iqtechmax.com/<path>).
# Cut pixel-for-pixel from the QR cards first shared on Oct 12, 2026.
QR_LOCK = {
    "mip-elite-pass.png": "bc75f49d9f24b97ed79cdb4f7962c5da883d52c7c3b6804206a6c5af3b995574",
    "vvip-pass.png": "76c5645178e0a520a53a99fa85e8c05876ae583623f5a8497ec182b2fed5a72c",
    "fanpit-pass.png": "74deeb59718d59551e3260d08ee8913a342954fb8054a4457ffab4f87b9c101e",
    "gold-pass.png": "2c0ffae4cc841372a9b8086e5025178fa5a8ffd5db95b67309f9ac363e41bc63",
    "silver-pass.png": "e55b9c7eb6646bb2dc33a8f3b71e0882dda111e045c067001d1731d9400847fa",
}

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOCS = os.path.join(ROOT, "docs")
CODE_DIR = os.path.join(ROOT, "qr", "code")


def check_files():
    missing = [p for p in QR_PATHS
               if not os.path.isfile(os.path.join(DOCS, p, "index.html"))]
    for p in missing:
        print(f"MISSING  docs/{p}/index.html")
    return missing


def check_qr_images():
    changed = []
    for name, digest in QR_LOCK.items():
        path = os.path.join(CODE_DIR, name)
        if not os.path.isfile(path):
            changed.append(name)
            print(f"MISSING  qr/code/{name}")
        elif hashlib.sha256(open(path, "rb").read()).hexdigest() != digest:
            changed.append(name)
            print(f"CHANGED  qr/code/{name}  (restore it: git checkout -- qr/code/{name})")
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
            print(f"{len(changed)} of {len(QR_LOCK)} frozen QR patterns are missing or changed in qr/code/.")
        if missing or changed:
            sys.exit(1)
        print(f"All {len(QR_PATHS)} printed QR links OK in docs/, all {len(QR_LOCK)} QR patterns unchanged.")
