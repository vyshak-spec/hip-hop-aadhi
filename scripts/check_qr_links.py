"""Fail if any printed QR code link would break.

The 5 paths below are printed on QR codes and must never change. This list is kept
separate from make_qr.py on purpose, so a change to the generator can't silently
change what is protected.

Usage:
  python scripts/check_qr_links.py                                  # check docs/ files
  python scripts/check_qr_links.py --live https://events.iqtechmax.com  # check the live site
"""
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

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")


def check_files():
    missing = [p for p in QR_PATHS
               if not os.path.isfile(os.path.join(DOCS, p, "index.html"))]
    for p in missing:
        print(f"MISSING  docs/{p}/index.html")
    return missing


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
        problems, where = check_live(sys.argv[2]), "on the live site"
    else:
        problems, where = check_files(), "in docs/"
    if problems:
        sys.exit(f"{len(problems)} of {len(QR_PATHS)} printed QR links are broken {where}.")
    print(f"All {len(QR_PATHS)} printed QR links OK {where}.")
