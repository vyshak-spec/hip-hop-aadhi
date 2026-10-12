"""Scan each QR image, fetch the live page, and check it shows that tier's pass and nothing else.

Usage: python verify_qr.py [SITE_ROOT]
SITE_ROOT replaces the domain in the scanned link, e.g.
https://vyshak-spec.github.io/hip-hop-aadhi/ (GitHub Pages) or http://localhost:8000/ to test
before the custom domain is live.
"""
import hashlib
import re
import sys
import urllib.parse
import urllib.request

import cv2

from make_qr import BASE_URL
from prepare_passes import PASS_DIR, TIERS


def fetch(url):
    return urllib.request.urlopen(url, timeout=20).read()


if __name__ == "__main__":
    detector = cv2.QRCodeDetector()
    domain = BASE_URL.split("/hiphop-aadhi/")[0] + "/"
    site_root = sys.argv[1] if len(sys.argv) > 1 else domain
    failed, seen = 0, set()
    for slug, name, price, _, _ in TIERS:
        img = cv2.resize(cv2.imread(f"qr/qr_{slug}.png"), None, fx=0.25, fy=0.25)
        scanned, _, _ = detector.detectAndDecode(img)
        url = scanned.replace(domain, site_root, 1)
        page = urllib.request.urlopen(url, timeout=20)  # follows the trailing-slash redirect
        html, url = page.read().decode(), page.geturl()
        badge = re.search(r'class="tier">([^<]*)', html).group(1)
        badge = badge.replace("&middot;", "·").replace("&#8377;", "Rs ")
        # every picture except the IQ Techmax mark must be this tier's pass
        passes = [s for s in re.findall(r'<img src="([^"]*)"', html) if "iqtechmax" not in s]
        same_pic = len(passes) == 1 and (
            hashlib.md5(fetch(urllib.parse.urljoin(url, passes[0]))).digest()
            == hashlib.md5(open(f"{PASS_DIR}/{slug}.jpg", "rb").read()).digest())
        ok = (scanned == BASE_URL + slug and scanned not in seen
              and badge == f"{name.upper()} · Rs {price}" and same_pic)
        seen.add(scanned)
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  qr_{slug}.png -> {scanned}  ({badge})")
    print(f"All {len(TIERS)} pass." if not failed else f"{failed} failed.")
    sys.exit(1 if failed else 0)
