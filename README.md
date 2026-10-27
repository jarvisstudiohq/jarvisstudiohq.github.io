# Jarvis Studios website

A small static site for the studio's games and the documents the app stores ask for: a Privacy Policy, Terms of Use, a
support page and data deletion instructions for every game. Plain HTML and CSS with two tiny scripts. No framework, no
build on the server, no cookies, no analytics, no trackers. The only outside request is Google Fonts.

## The support email

The studio's support email is **one value**, in `assets/js/config.js` (`supportEmail`, currently `jarvisstudiohq@gmail.com`).
To change it:

1. Edit `supportEmail` in `assets/js/config.js`.
2. Run `python3 tools/build.py` (writes the address into every page too, for visitors without JavaScript).
3. Run `python3 tools/check.py --release` (fails if the address is still a placeholder).

The game's own documents name the same address (Terms section 15, Privacy Policy section 11, and Settings › About › Contact us), so a change
also means a new version of those documents in the game, copied into `content/turnstone/`.

Every page shows the address from that one value. Nothing else in the site holds an email address except the game's legal text, and the check fails if any other address is hard-coded.

## What is where

| Path | What it is |
|---|---|
| `index.html`, `games/`, `support/`, `legal/` | The four tabs: Home, Games, Support, Legal |
| `turnstone/` | Turnstone's game page |
| `turnstone/terms/`, `turnstone/privacy/` | Turnstone's Terms of Use and Privacy Policy, generated word for word from the game's text |
| `turnstone/delete-data/` | How "Delete my data" works in the game |
| `turnstone/support/` | Turnstone support and FAQ |
| `hot-crumb/` and `hot-crumb/terms/`, `privacy/`, `support/` | Hot Crumb's game page, and placeholders marked "Not yet published" |
| `404.html` | The page-not-found page (works at any depth, see below) |
| `content/turnstone/*.txt` | Exact copies of the game's `godot-production/legal/*.txt` |
| `assets/` | CSS, the two scripts, images |
| `tools/build.py` | Writes every HTML page from one layout |
| `tools/check.py` | Checks links, paths, the legal text, the email and image sizes |
| `site-root.txt`, `.nojekyll` | Keep them. The 404 page uses `site-root.txt` to find the site root. `.nojekyll` tells GitHub Pages to serve the files as they are |

The HTML is committed, so GitHub Pages serves the folder as it is. Edit pages in `tools/build.py` (and the CSS in
`assets/css/site.css`), then run `python3 tools/build.py` and `python3 tools/check.py`.

### Relative links only

Every link and asset path is relative (`../legal/`, never `/legal/`), so the same files work at a domain root
(`https://jarvisstudiohq.github.io/`) and under a subpath (`https://cjarvis0.github.io/jarvis-studio/`). The check fails on
any root-absolute path or any `github.io` address in a page. The only place an absolute address may go is the optional
`siteUrl` in `assets/js/config.js`, and you can leave it empty.

GitHub Pages serves `404.html` for a missing address at any depth, where relative links would point to the wrong place.
The 404 page has its styles and art inline, and a few lines of script find the site root: `siteUrl` if you set it
(re-run the build after setting it), otherwise the nearest parent folder that has `site-root.txt`.

## When a game's legal text changes

The site must match the game word for word.

1. Copy the game's `godot-production/legal/terms_of_use.txt` and `privacy_policy.txt` into `content/turnstone/`.
2. Run `python3 tools/build.py`. The version and effective date come from each file's `@meta` line.
3. Run `python3 tools/check.py --game-legal <path to the game>/godot-production/legal`. This also confirms the copies
   are identical to the game's files, and that the game has no legal document the site is missing.
4. If the game's "Delete my data" flow changed, update `turnstone/delete-data/` in `tools/build.py` so it describes the flow exactly.

Hot Crumb has no legal text yet. When it does, add its `.txt` files under `content/hot-crumb/` and build its pages the
same way Turnstone's are built (`build_legal_doc` in `tools/build.py`).

## Check locally

```sh
python3 tools/build.py
python3 tools/check.py                        # add --release before publishing
python3 -m http.server 8000                   # then open http://localhost:8000/
```

`python3 -m http.server` does not serve `404.html` for missing pages. GitHub Pages does.

## Publish on GitHub Pages

The owner's personal account already uses its one user site (`cjarvis0.github.io`), so there are two ways to host this.
**Option A is recommended:** your personal site stays separate, and the store URLs are short and clean.

### Option A (recommended): a free GitHub organization, site at the root

1. On GitHub: your profile picture › **Your organizations** › **New organization** › choose the **Free** plan. Name it
   `jarvisstudiohq` (already chosen). The site address will be `https://jarvisstudiohq.github.io/`.
2. In the organization, create a **public** repository named exactly `jarvisstudiohq.github.io` (the organization name
   plus `.github.io`). Don't add a README, .gitignore or license, so the repository stays empty.
3. Push this folder:
   ```sh
   cd jarvis-studio-site   # this folder
   git remote add origin https://github.com/jarvisstudiohq/jarvisstudiohq.github.io.git
   git push -u origin main
   ```
4. In the repository: **Settings** › **Pages** › **Build and deployment** › Source: **Deploy from a branch** ›
   Branch: `main`, folder `/ (root)` › **Save**. (User and organization sites usually turn this on by themselves. Check it anyway.)
5. Wait a minute or two, then open `https://jarvisstudiohq.github.io/`. **Settings › Pages** shows the live address.
6. Leave **Enforce HTTPS** on.

Store URLs for option A:

| What | URL |
|---|---|
| Turnstone Privacy Policy | `https://jarvisstudiohq.github.io/turnstone/privacy/` |
| Turnstone Terms of Use | `https://jarvisstudiohq.github.io/turnstone/terms/` |
| Turnstone support | `https://jarvisstudiohq.github.io/turnstone/support/` |
| Turnstone data deletion | `https://jarvisstudiohq.github.io/turnstone/delete-data/` |
| Marketing / game page | `https://jarvisstudiohq.github.io/turnstone/` |
| Hot Crumb privacy (placeholder) | `https://jarvisstudiohq.github.io/hot-crumb/privacy/` |

### Option B: a project site under your personal account

1. On your personal account, create a **public** repository, for example `jarvis-studio`. Don't add any files, so it stays empty.
2. Push this folder:
   ```sh
   cd jarvis-studio-site   # this folder
   git remote add origin https://github.com/cjarvis0/jarvis-studio.git
   git push -u origin main
   ```
3. In the repository: **Settings** › **Pages** › Source: **Deploy from a branch** › Branch: `main`, folder `/ (root)` › **Save**.
4. After a minute or two the site is at `https://cjarvis0.github.io/jarvis-studio/`.

Store URLs for option B:

| What | URL |
|---|---|
| Turnstone Privacy Policy | `https://cjarvis0.github.io/jarvis-studio/turnstone/privacy/` |
| Turnstone Terms of Use | `https://cjarvis0.github.io/jarvis-studio/turnstone/terms/` |
| Turnstone support | `https://cjarvis0.github.io/jarvis-studio/turnstone/support/` |
| Turnstone data deletion | `https://cjarvis0.github.io/jarvis-studio/turnstone/delete-data/` |
| Marketing / game page | `https://cjarvis0.github.io/jarvis-studio/turnstone/` |
| Hot Crumb privacy (placeholder) | `https://cjarvis0.github.io/jarvis-studio/hot-crumb/privacy/` |

If you later set a custom domain on your personal site, project sites move under it too (for example
`https://yourname.com/jarvis-studio/`). That is another reason to prefer option A.

### Where to paste the URLs

**App Store Connect** (iOS):
- Your app › **App Information** › **Privacy Policy URL**: the Privacy Policy URL.
- Your app › the version page › **Support URL**: the Turnstone support URL. **Marketing URL** (optional): the game page.
- For a custom license agreement, App Information › **License Agreement** › Edit, and use the Terms of Use. Otherwise
  Apple's standard license applies, and the Terms are still linked from the game.

**Google Play Console** (Android):
- **Policy and programs › App content › Privacy policy**: the Privacy Policy URL.
- **Grow users › Store presence › Store settings › Store listing contact details**: the support email (the same one as in
  `config.js`) and, as **Website**, the game page or the support URL.
- **App content › Data safety**: if Play asks for a data deletion link, use the data deletion URL. (Today the game has no
  account and keeps everything on the device. The page explains the in-game "Delete my data" flow.)

Open each URL in a private browser window before pasting it, to be sure it is live.

## Adding a custom domain later

You can move the site to your own domain (for example `jarvisstudios.com`) at any time. All links are relative, so nothing in the pages changes.

1. Buy the domain from any registrar.
2. Verify it for your account or organization first: **Settings** (of the organization or your account) › **Pages** ›
   **Add a domain**, then add the TXT record GitHub shows at your registrar. This stops anyone else from claiming it.
3. In the site's repository: **Settings › Pages › Custom domain**: enter the domain › **Save**. GitHub adds a `CNAME`
   file to the repository. Run `git pull` so your local copy has it too.
4. At your registrar, add the DNS records from GitHub's guide, "Managing a custom domain for your GitHub Pages site":
   for an apex domain (`jarvisstudios.com`), `A` records to GitHub's Pages IP addresses (and the `AAAA` records for IPv6);
   for `www`, a `CNAME` to `jarvisstudiohq.github.io`. Use the addresses from the guide, not from memory.
5. When the DNS check passes, turn on **Enforce HTTPS**.
6. Optionally set `siteUrl` in `assets/js/config.js` to `https://jarvisstudios.com/` and rebuild.
7. Update the URLs in App Store Connect and Play Console. GitHub redirects the old `github.io` addresses to the custom
   domain, but the stores should hold the final ones.

With option B, the custom domain applies to your personal site and every project site under it. A domain just for the
studio is simpler with option A.

## Privacy of this website

No cookies, local storage, analytics, ads, forms or third-party scripts. `tools/check.py` fails if any of these show up.
The fonts (Grandstander, Fredoka and Ultra, all under the SIL Open Font License) load from Google Fonts. To avoid
that request, download the font files, put them in `assets/fonts/`, replace the Google Fonts `<link>` in
`tools/build.py` with `@font-face` rules in the CSS, and update the "This website" section on the Legal page.

The JARVIS / STUDIOS wordmark is drawn in CSS with Ultra, the closest freely licensed match to the slab lettering on the
game's studio card. No proprietary font is included.
