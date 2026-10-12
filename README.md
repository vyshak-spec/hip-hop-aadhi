# Hiphop Aadhi – Star Galatta Salem 2026 – Booking Pass QR Codes

Five fixed QR codes, one per booking level, for Star Galatta Salem 2026 (Sat Oct 31, 5–10 PM,
Vysya College, Salem). Each QR code opens only its own pass: the full ticket design followed by the
pass name, price and event details.

The site is the static `docs/` folder, served at `https://events.iqtechmax.com/hiphop-aadhi/`.
The pages are marked `noindex` and there is no index page linking them, so a pass page is reached
by scanning its QR code (the links are not secret: anyone with the URL can open it).

> **Testing phase:** the QR images in `qr/` currently point to the GitHub Pages copy
> (`https://vyshak-spec.github.io/hip-hop-aadhi/hiphop-aadhi/<level>-pass`). Do not print them.
> After the Hostinger server is set up, switch `BASE_URL` in `make_qr.py` to the
> `events.iqtechmax.com` line, run `python make_qr.py`, and push; those are the codes to print.

| Level | Price | QR image | Final QR link |
|---|---|---|---|
| MIP Elite Pass | Rs 25,000 | `qr/qr_mip-elite-pass.png` | https://events.iqtechmax.com/hiphop-aadhi/mip-elite-pass |
| VVIP Pass | Rs 10,000 | `qr/qr_vvip-pass.png` | https://events.iqtechmax.com/hiphop-aadhi/vvip-pass |
| Fanpit Pass | Rs 2,499 | `qr/qr_fanpit-pass.png` | https://events.iqtechmax.com/hiphop-aadhi/fanpit-pass |
| Gold Pass | Rs 1,099 | `qr/qr_gold-pass.png` | https://events.iqtechmax.com/hiphop-aadhi/gold-pass |
| Silver Pass | Rs 599 | `qr/qr_silver-pass.png` | https://events.iqtechmax.com/hiphop-aadhi/silver-pass |

## How updates work

1. Edit the content (a ticket design → re-run `prepare_passes.py`; the page template in `make_qr.py`),
   then run `python make_qr.py` to rebuild `docs/`.
2. Commit and push to `main`.
3. GitHub Actions checks that all 5 printed QR links still exist, then updates the server
   automatically. Progress is on the repo's **Actions** tab.

**Once the QR codes are printed, never rename or move these 5 folders in `docs/`:**

```
hiphop-aadhi/mip-elite-pass    hiphop-aadhi/gold-pass
hiphop-aadhi/vvip-pass         hiphop-aadhi/silver-pass
hiphop-aadhi/fanpit-pass
```

If one must move, keep the old folder with an `index.html` that redirects to the new place.
A push that removes any of them fails the check and is not deployed (`scripts/check_qr_links.py`).
Changing a ticket design is safe: the picture changes, the QR link does not.

## Server setup (one time, Nginx)

The same server already hosts `events.iqtechmax.com` (GenZ Bhajan). Clone this repo next to it:

```sh
cd /var/www
git clone https://github.com/vyshak-spec/hip-hop-aadhi.git
```

and add this block inside the existing `server { ... server_name events.iqtechmax.com; ... }`,
then `sudo nginx -t && sudo systemctl reload nginx`:

```nginx
location /hiphop-aadhi/ {
    root /var/www/hip-hop-aadhi/docs;
    try_files $uri $uri/ =404;
}
```

Auto-deploy (`.github/workflows/deploy.yml`) needs the repo secrets `DEPLOY_HOST`, `DEPLOY_USER`
and `DEPLOY_SSH_KEY` (same values as the GenZ Bhajan repo). Until they are set the deploy step is
skipped with a warning.

Optional test copy on GitHub Pages: Settings → Pages → Deploy from branch `main`, folder `/docs`.
It is then at `https://vyshak-spec.github.io/hip-hop-aadhi/hiphop-aadhi/<level>-pass`.

## Layout

- `qr/` – the 5 printable QR images
- `passes/` – web-ready sRGB pass images (2200 px wide)
- `docs/` – the published site (generated)
- `prepare_passes.py` – the list of 5 levels; converts the designer's CMYK ticket files
  (`* Ticket.jpg.jpeg`, ~5 MB each, not committed; place them in the project root) into `passes/`
- `make_qr.py` – builds `docs/` and the QR images (`BASE_URL` sets the link)
- `verify_qr.py` – scans each QR and checks the live page shows that level's pass and nothing else
- `scripts/check_qr_links.py` – fails if any of the 5 printed QR paths is missing (`--live URL` checks the site)
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
`python verify_qr.py http://localhost:8000/`.
