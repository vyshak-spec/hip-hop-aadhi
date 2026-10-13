# Hiphop Aadhi – Star Galatta Salem 2026 – Booking Pass QR Codes

Five fixed QR codes, one per booking level, for Star Galatta Salem 2026 (Sat Oct 31, 5–10 PM,
Vysya College, Salem). Each QR code opens only its own pass: the full ticket design followed by the
pass name, price and event details.

The site is the static `docs/` folder, served at `https://events.iqtechmax.com/star-galatta/`.
The pages are marked `noindex` and there is no index page linking them, so a pass page is reached
by scanning its QR code (the links are not secret: anyone with the URL can open it).

**The 5 QR patterns are frozen.** Each pattern is stored once in `qr/code/` and never redrawn:
`make_qr.py` builds the printable card in `qr/` by pasting that exact pattern and drawing the label
(pass name, price) under it, and `scripts/check_qr_links.py` holds the fingerprint (SHA-256) of each
pattern, so any push that changes one fails and is not deployed. Renaming a pass, changing a price,
a ticket design or the page layout changes the page and the label, never the QR pattern.

| Level | Price | QR image | QR link (fixed) |
|---|---|---|---|
| MIP Elite Pass | Rs 25,000 | `qr/qr_mip-elite-pass.png` | https://events.iqtechmax.com/star-galatta/mip-elite-pass |
| VVIP Pass | Rs 10,000 | `qr/qr_vvip-pass.png` | https://events.iqtechmax.com/star-galatta/vvip-pass |
| Gold Pass | Rs 2,499 | `qr/qr_fanpit-pass.png` | https://events.iqtechmax.com/star-galatta/fanpit-pass |
| Silver Pass | Rs 1,099 | `qr/qr_gold-pass.png` | https://events.iqtechmax.com/star-galatta/gold-pass |
| Bronze Pass | Rs 599 | `qr/qr_silver-pass.png` | https://events.iqtechmax.com/star-galatta/silver-pass |

On Oct 13, 2026 ARI Entertainment renamed three levels (Fan Pit → Gold, Gold → Silver,
Silver → Bronze, prices unchanged). The links keep the old names on purpose, since they are
inside the QR codes; only the names shown on the pages, the QR labels and the ticket pictures
changed (`TIERS` in `prepare_passes.py`). The designer's artwork still prints the old names, so
`prepare_passes.py` rewrites the name on each picture's side strip with `relabel.py` (same font,
size, spacing and gold/silver finish; the price line and the rest of the artwork are untouched).
If the designer sends updated artwork, set its printed name in `PRINTED` and the step is skipped.

## How updates work

1. Edit the content (a ticket design → re-run `prepare_passes.py`; the page template in `make_qr.py`),
   then run `python make_qr.py` to rebuild `docs/`.
2. Commit and push to `main`.
3. GitHub Actions checks that all 5 printed QR links still exist and all 5 QR patterns are
   unchanged, then updates the server automatically. Progress is on the repo's **Actions** tab.

**Never rename or move these 5 folders in `docs/`:**

```
star-galatta/mip-elite-pass    star-galatta/gold-pass
star-galatta/vvip-pass         star-galatta/silver-pass
star-galatta/fanpit-pass
```

If one must move, keep the old folder with an `index.html` that redirects to the new place.
A push that removes any of them fails the check and is not deployed (`scripts/check_qr_links.py`).
Changing a ticket design is safe: the picture changes, the QR link does not.

## Server setup (one time, Hostinger VPS, Nginx)

The QR codes only work once this is done. The same Hostinger VPS already hosts
`events.iqtechmax.com` (GenZ Bhajan), so no DNS change is needed. SSH in and clone this repo next to it:

```sh
cd /var/www
git clone https://github.com/vyshak-spec/hip-hop-aadhi.git
```

The Nginx file `/etc/nginx/sites-enabled/events` belongs to GenZ Bhajan, so this site's settings live
in their own file, `/etc/nginx/snippets/star-galatta.conf`:

```nginx
location ^~ /star-galatta/ {
    root /var/www/hip-hop-aadhi/docs;
    try_files $uri $uri/ =404;
}
```

The only change to the GenZ Bhajan file is one line in its HTTPS (`listen 443 ssl`) server block,
`include snippets/star-galatta.conf;`. Then `sudo nginx -t && sudo systemctl reload nginx`.

Auto-deploy (`.github/workflows/deploy.yml`) needs the repo secrets `DEPLOY_HOST`, `DEPLOY_USER`
and `DEPLOY_SSH_KEY` (same values as the GenZ Bhajan repo). Until they are set the deploy step is
skipped with a warning.

Then check: `python scripts/check_qr_links.py --live https://events.iqtechmax.com` and `python verify_qr.py`.

A preview copy is also on GitHub Pages (from `main`, folder `/docs`), opened by typing the link:
`https://vyshak-spec.github.io/hip-hop-aadhi/star-galatta/<level>-pass`. The QR codes do not use it.

## Layout

- `qr/` – the 5 printable QR cards (frozen pattern + current label)
- `qr/code/` – the 5 frozen QR patterns (never edit)
- `passes/` – web-ready sRGB pass images (2200 px wide)
- `docs/` – the published site (generated)
- `prepare_passes.py` – the list of 5 levels; converts the designer's CMYK ticket files
  (`* Ticket.jpg.jpeg`, ~5 MB each, not committed; place them in the project root) into `passes/`,
  replacing a printed name that no longer matches the level (`PRINTED`)
- `relabel.py` – rewrites the pass name on a ticket's side strip in the artwork's own style
- `fonts/` – Bebas Neue, the artwork's font (SIL Open Font License, `fonts/OFL.txt`)
- `make_qr.py` – builds `docs/` and the QR cards from the frozen patterns (`BASE_URL` is the frozen link)
- `verify_qr.py` – scans each QR and checks the live page shows that level's pass and nothing else
- `scripts/check_qr_links.py` – fails if any of the 5 printed QR paths is missing or any QR pattern changed
  (`--live URL` checks the site)
- `.github/workflows/deploy.yml` – on every push to `main`: QR link check → deploy to server → live check

## Rebuild

```sh
pip install -r requirements.txt
python prepare_passes.py   # only if a ticket design changes
python make_qr.py
python scripts/check_qr_links.py   # same check the deploy runs
git add . && git commit -m "Update pass pages" && git push
python verify_qr.py        # after the deploy finishes
```

To test before the server is set up: `cd docs && python -m http.server 8000`, then
`python verify_qr.py http://localhost:8000/`, or against the preview:
`python verify_qr.py https://vyshak-spec.github.io/hip-hop-aadhi/`.
