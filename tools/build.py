#!/usr/bin/env python3
"""Builds every HTML page of the Jarvis Studios website from one layout.

    python3 tools/build.py

The output is plain HTML committed next to this script's folder, so GitHub Pages serves the site as it is (no build runs there).
Run this after changing a page below, the support email in assets/js/config.js, or a legal text in content/.

Rules the output follows (tools/check.py verifies them):
- Every link and asset path is relative (no leading "/"), so the site works both at a domain root
  (https://jarvisstudiohq.github.io/) and under a subpath (https://cjarvis0.github.io/jarvis-studio/).
- Each game's legal pages are generated from content/<game>/*.txt, verbatim copies of the game's own legal files.
- The support email has one source: supportEmail in assets/js/config.js.
- A store badge renders (linked) only once that store URL is set in GAMES below; until then a text label shows the status.
- Social links show only once SOCIAL below lists one.
"""

import datetime
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO = "Jarvis Studios"
FONTS = ("https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600"
         "&family=Grandstander:wght@700;800;900&family=Ultra&display=swap")
YEAR = datetime.date.today().year
R = "{rel}"   # placeholder for the relative path to the site root, filled in by page()

# The header nav. "games" opens a dropdown (GAME_LINKS); the others are plain links.
NAV = [("games", "Games", "games/"), ("news", "News", "news/"), ("support", "Support", "support/"), ("about", "About", "about/")]
GAME_LINKS = [("Turnstone", "turnstone/", "Cozy tile puzzle"), ("Tumble", "tumble/", "Drop-and-fuse block puzzle")]

# Store pages. Leave a URL empty while the game is not in that store: the badge then shows "Coming soon" and is not a link.
GAMES = {
    "turnstone": {"name": "Turnstone", "app_store": "", "google_play": "", "status": "Coming soon to iOS and Android"},
    "tumble": {"name": "Tumble", "app_store": "", "google_play": "", "status": "Coming soon to iOS and Android"},
}

# Social profiles: (label, url). Empty on purpose: nothing shows until the studio has accounts.
SOCIAL = []


def esc(s):
    return html.escape(s, quote=True)


def read_config():
    """The two values in assets/js/config.js: supportEmail (required) and siteUrl (optional)."""
    src = (ROOT / "assets/js/config.js").read_text(encoding="utf-8")
    m = re.search(r'supportEmail\s*:\s*"([^"]*)"', src)
    if not m:
        sys.exit("build: supportEmail not found in assets/js/config.js")
    u = re.search(r'siteUrl\s*:\s*"([^"]*)"', src)
    return m.group(1).strip(), (u.group(1).strip() if u else "")


EMAIL, SITE_URL = read_config()


def email_link(subject=""):
    href = "mailto:" + EMAIL + ("?subject=" + subject.replace(" ", "%20") if subject else "")
    sub = f' data-subject="{esc(subject)}"' if subject else ""
    return f'<a data-support-email{sub} href="{esc(href)}">{esc(EMAIL)}</a>'


# ---------------------------------------------------------------- legal text (the game's files, verbatim)

def parse_legal(path):
    """content/<game>/<doc>.txt -> (meta dict, blocks). A block is ("h", text), ("p", text) or ("ul", [items]).
    The file format is the game's: an @meta JSON line, '# ' headings, paragraphs separated by blank lines, '• ' list items."""
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines[0].startswith("@meta "):
        sys.exit(f"build: {path} has no @meta line")
    meta = json.loads(lines[0][6:])
    paras = [p.strip() for p in "\n".join(lines[1:]).split("\n\n") if p.strip()]
    blocks = []
    for p in paras:
        if p.startswith("# "):
            blocks.append(("h", p[2:].strip()))
        elif p.startswith("• "):
            if blocks and blocks[-1][0] == "ul":
                blocks[-1][1].append(p[2:].strip())
            else:
                blocks.append(("ul", [p[2:].strip()]))
        else:
            blocks.append(("p", p))
    return meta, blocks


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def legal_html(blocks):
    out = []
    for kind, val in blocks:
        if kind == "h":
            out.append(f'<h2 id="{slug(val)}">{esc(val)}</h2>')
        elif kind == "p":
            out.append(f"<p>{esc(val)}</p>")
        else:
            out.append("<ul>\n" + "\n".join(f"<li>{esc(i)}</li>" for i in val) + "\n</ul>")
    return "\n".join(out)


def nice_date(iso):
    y, m, d = iso.split("-")
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
              "November", "December"]
    return f"{months[int(m) - 1]} {int(d)}, {y}"


TS_TERMS_META, TS_TERMS = parse_legal(ROOT / "content/turnstone/terms_of_use.txt")
TS_PRIV_META, TS_PRIV = parse_legal(ROOT / "content/turnstone/privacy_policy.txt")
TB_TERMS_META, TB_TERMS = parse_legal(ROOT / "content/tumble/terms_of_use.txt")
TB_PRIV_META, TB_PRIV = parse_legal(ROOT / "content/tumble/privacy_policy.txt")


# ---------------------------------------------------------------- images

def pic(base, widths, sizes, alt, w, h, cls="", eager=False, fallback="jpg", fallback_w=None, img_attrs=""):
    """A <picture> with WebP sources at several widths and a JPEG/PNG fallback. base is relative to assets/img/."""
    b = f"{R}assets/img/{base}"
    fw = fallback_w or widths[0]
    load = ' fetchpriority="high"' if eager else ' loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    srcset = ", ".join(f"{b}-{x}.webp {x}w" for x in widths)
    return (f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">'
            f'<img{c} src="{b}-{fw}.{fallback}" width="{w}" height="{h}" alt="{esc(alt)}"{load} decoding="async"{img_attrs}></picture>')


def otto(cls="cutout", alt="Otto, a round purple octopus, waving two arms and grinning", sizes="(min-width: 900px) 320px, 46vw"):
    return pic("turnstone/otto", [320, 640], sizes, alt, 640, 542, cls=cls, fallback="png", fallback_w=640)


def tumble_icon(cls="tb-icon", sizes="(min-width: 900px) 300px, 60vw"):
    return pic("tumble/icon", [256, 512], sizes, "The Tumble app icon: the word TUMBLE in chunky candy-colored blocks on a deep purple background", 512, 512, cls=cls, eager=True, fallback="png", fallback_w=512)


def cat(kind="look", cls="cat", alt=""):
    w, h = (48, 44)
    return f'<img class="{cls}" src="{R}assets/img/studio/cat-{kind}.svg" width="{w}" height="{h}" alt="{esc(alt)}" loading="lazy" decoding="async">'


# ---------------------------------------------------------------- store badges

def store_badges(key, compact=False):
    """Where to get a game. A store's official badge (assets/img/store/, unmodified) renders only once that store's URL is set
    in GAMES, and then always as a link to the store page, as Apple's and Google's badge guidelines ask. Until a game has a
    store URL, a plain text label shows its status instead ("Coming soon to iOS and Android", "In development")."""
    g = GAMES[key]
    items = []
    for store, alt, src, cls in (
            ("app_store", "Download on the App Store", "store/app-store-badge.svg", "apple"),
            ("google_play", "Get it on Google Play", "store/google-play-badge.png", "google")):
        if g[store]:
            img = (f'<img class="badge-img {cls}" src="{R}assets/img/{src}" alt="{alt}" width="{120 if cls == "apple" else 646}" '
                   f'height="{40 if cls == "apple" else 250}" loading="lazy" decoding="async">')
            items.append(f'<li><a class="store-link" href="{esc(g[store])}">{img}</a></li>')
    cls = "store-badges compact" if compact else "store-badges"
    if not items:
        return f'<p class="store-status{" compact" if compact else ""}">{esc(g["status"])}</p>'
    return f'<ul class="{cls}" aria-label="Get {esc(g["name"])}">' + "".join(items) + "</ul>"


# ---------------------------------------------------------------- layout

def nav_html(rel, current):
    items = []
    for key, label, href in NAV:
        cur = ' aria-current="page"' if key == current else ""
        if key == "games":
            sub = "".join(f'<li><a href="{rel}{h}"><span class="sub-name">{esc(n)}</span><span class="sub-meta">{esc(m)}</span></a></li>'
                          for n, h, m in GAME_LINKS)
            sub += f'<li class="sub-all"><a href="{rel}{href}">All games</a></li>'
            mark = ' data-current="true"' if key == current else ""
            items.append(f'<li class="has-sub"{mark}><button class="nav-link sub-toggle" type="button" aria-expanded="false" aria-controls="games-menu">'
                         f'{label}<svg class="chev" viewBox="0 0 12 8" width="12" height="8" aria-hidden="true"><path d="M1 1.5 6 6.5 11 1.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
                         f'<ul class="sub" id="games-menu">{sub}</ul></li>')
        else:
            items.append(f'<li><a class="nav-link" href="{rel}{href}"{cur}>{label}</a></li>')
    return "\n".join(items)


def footer_html(rel):
    home = rel or "./"
    social = ""
    if SOCIAL:
        social = ('<div class="foot-col"><h2 class="foot-h">Follow us</h2><ul class="foot-links">'
                  + "".join(f'<li><a href="{esc(u)}">{esc(n)}<span class="sr-only"> (opens another site)</span></a></li>' for n, u in SOCIAL)
                  + "</ul></div>")
    badges = "".join(f'<div class="foot-game"><a class="foot-game-name" href="{rel}{k}/">{esc(g["name"])}</a>{store_badges(k, compact=True)}</div>'
                     for k, g in GAMES.items())
    return f"""<footer class="site-footer">
<div class="foot-cat" aria-hidden="true">{cat("nap", "cat-nap")}</div>
<div class="wrap foot-grid">
<div class="foot-brand">
<a class="wordmark on-dark" href="{home}" aria-label="{STUDIO}, home"><span class="wm-top" aria-hidden="true">JARVIS</span><span class="wm-bottom" aria-hidden="true">STUDIOS</span></a>
<p>Hand-made games for one thumb.</p>
<p class="foot-email">Support: {email_link()}</p>
<p class="foot-note">Our games are free to play, supported by ads and optional in-app purchases.</p>
</div>
<div class="foot-col foot-stores"><h2 class="foot-h">Get our games</h2>{badges}</div>
<div class="foot-col"><h2 class="foot-h">Studio</h2><ul class="foot-links">
<li><a href="{rel}games/">Games</a></li>
<li><a href="{rel}news/">News</a></li>
<li><a href="{rel}about/">About</a></li>
<li><a href="{rel}press/">Press kit</a></li>
<li><a href="{rel}support/">Support</a></li>
</ul></div>
<div class="foot-col"><h2 class="foot-h">Legal</h2><ul class="foot-links">
<li><a href="{rel}turnstone/terms/">Turnstone Terms of Use</a></li>
<li><a href="{rel}turnstone/privacy/">Turnstone Privacy Policy</a></li>
<li><a href="{rel}tumble/terms/">Tumble Terms of Use</a></li>
<li><a href="{rel}tumble/privacy/">Tumble Privacy Policy</a></li>
<li><a href="{rel}accessibility/">Accessibility statement</a></li>
<li><a href="{rel}legal/">All legal documents</a></li>
</ul></div>
{social}
</div>
<div class="wrap foot-base">
<p>© {YEAR} {STUDIO}. This website uses no cookies, no analytics and no trackers. <a href="{rel}legal/#this-website">About this website</a></p>
</div>
</footer>""".replace(R, rel)


def page(path, title, description, nav, body, crumbs=None, wide=False, body_class=""):
    """path: the output folder relative to the site root ("" for the home page, "turnstone/privacy/" ...).
    wide=True: the body brings its own full-width sections (and .wrap where it wants one)."""
    depth = path.count("/")
    rel = "../" * depth
    home = rel or "./"
    full_title = title if title == STUDIO else f"{title} · {STUDIO}"
    crumb_html = ""
    if crumbs:
        items = []
        for label, href in crumbs:
            if href is None:
                items.append(f'<li aria-current="page">{esc(label)}</li>')
            else:
                items.append(f'<li><a href="{rel}{href}">{esc(label)}</a></li>' if href else
                             f'<li><a href="{home}">{esc(label)}</a></li>')
        crumb_html = f'<nav class="breadcrumb" aria-label="Breadcrumb"><ol>{"".join(items)}</ol></nav>\n'
    inner = body.replace(R, rel).replace("{home}", home)
    if wide:
        cw = f'<div class="wrap crumb-wrap">{crumb_html}</div>\n' if crumb_html else ""
        main = f'<main id="main" tabindex="-1" class="main-wide">\n{cw}{inner}\n</main>'
    else:
        main = f'<main id="main" tabindex="-1">\n<div class="wrap">\n{crumb_html}{inner}\n</div>\n</main>'
    bc = f' class="{body_class}"' if body_class else ""
    doc = f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#fff6e4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#10232a" media="(prefers-color-scheme: dark)">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{rel}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{rel}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{rel}assets/css/site.css">
<script>document.documentElement.classList.add("js");</script>
</head>
<body{bc}>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
<div class="wrap header-row">
<a class="wordmark" href="{home}" aria-label="{STUDIO}, home"><span class="wm-top" aria-hidden="true">JARVIS</span><span class="wm-bottom" aria-hidden="true">STUDIOS</span></a>
<button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav"><span class="menu-icon" aria-hidden="true"><span></span><span></span><span></span></span><span class="menu-label">Menu</span></button>
<nav class="site-nav" id="site-nav" aria-label="Main">
<ul class="nav-list">
{nav_html(rel, nav)}
</ul>
</nav>
</div>
</header>
{main}
{footer_html(rel)}
<script src="{rel}assets/js/config.js"></script>
<script src="{rel}assets/js/site.js"></script>
</body>
</html>
"""
    out = ROOT / path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    return out


def stamp(version, date, label="Version"):
    return (f'<ul class="doc-stamp"><li>{label} {esc(str(version))}</li>'
            f'<li>Effective <time datetime="{date}">{nice_date(date)}</time></li></ul>')


# ---------------------------------------------------------------- shared copy

TS_PITCH = ("Turnstone is a cozy tile puzzle set in a sunny harbor town, starring Otto, a round purple octopus who's never in a hurry, "
            "and hopes you won't be either. It's turn-based and made for one thumb: tap a tile to flip the path between two matching "
            "Twins, and three or more matching tiles clear. Take your time. There are no timers, no lives and no energy, so nothing "
            "ever makes you wait to keep playing.")
TB_PITCH = ("Tumble is a drop-and-fuse block puzzle for one thumb, played in portrait. Tetris-shaped pieces drop into a well. "
            "When two pieces of the same size touch, they fuse into a bigger one, and fused pieces can chain. Full rows clear, "
            "and two of the biggest pieces make a Tumble.")

# The studio's plain statement about ads and purchases (the games' own Terms and Privacy Policy are the full text).
ADS_LINE = "Our games are free to play, supported by ads and optional in-app purchases."
ADS_DETAIL = ("Ads and purchases are not switched on yet. When they are, ads are optional rewarded ads. We may later add an occasional ad "
              "between runs in Tumble's Classic mode. Ads never appear in a ranked Daily, and Remove ads is available.")

PAGE_DATE = "2026-10-27"    # the date the support, deletion and placeholder pages were written
SUPPORT_VERSION = 1


def turnstone_docs_list(rel_prefix=R):
    tv, td = TS_TERMS_META["version"], TS_TERMS_META["effective_date"]
    pv, pd = TS_PRIV_META["version"], TS_PRIV_META["effective_date"]
    rows = [
        ("turnstone/terms/", "Terms of Use", f"Version {tv} · {nice_date(td)}"),
        ("turnstone/privacy/", "Privacy Policy", f"Version {pv} · {nice_date(pd)}"),
        ("turnstone/delete-data/", "Delete your data", "How “Delete my data” works"),
        ("turnstone/support/", "Support and FAQ", "Questions and contact"),
    ]
    return '<ul class="doc-list">\n' + "\n".join(
        f'<li><a href="{rel_prefix}{h}"><span class="doc-name">{n}</span><span class="doc-meta">{m}</span></a></li>'
        for h, n, m in rows) + "\n</ul>"


def tumble_docs_list(rel_prefix=R):
    tv, td = TB_TERMS_META["version"], TB_TERMS_META["effective_date"]
    pv, pd = TB_PRIV_META["version"], TB_PRIV_META["effective_date"]
    rows = [
        ("tumble/terms/", "Terms of Use", f"Version {tv} · {nice_date(td)}"),
        ("tumble/privacy/", "Privacy Policy", f"Version {pv} · {nice_date(pd)}"),
        ("tumble/delete-data/", "Delete your data", "How “Delete my data” works"),
        ("tumble/support/", "Support and FAQ", "Questions and contact"),
    ]
    return '<ul class="doc-list">\n' + "\n".join(
        f'<li><a href="{rel_prefix}{h}"><span class="doc-name">{n}</span><span class="doc-meta">{m}</span></a></li>'
        for h, n, m in rows) + "\n</ul>"


# ---------------------------------------------------------------- news

NEWS = [
    {
        "slug": "tumble-in-development",
        "title": "Tumble is in development",
        "tag": "Tumble", "tag_class": "grape",
        "date": "2026-10-29",
        "thumb_alt": "Two phones on a purple background: Tumble's Home screen with its candy-colored logo, and a board where two giant blocks have just made a Tumble",
        "summary": "Our second game is a bright, drop-and-fuse block puzzle for one thumb. It's still in development, and here's what we can share.",
        "body": f"""<p class="lead">Our second game is Tumble, a bright, drop-and-fuse block puzzle for one thumb. It's still in development.</p>
<p>Tetris-shaped pieces drop into a well. When two pieces of the same size touch, they fuse into a bigger one, and fused pieces can chain. Full rows clear, and two of the biggest pieces make a Tumble.</p>
<p>A rising floor slowly pushes the rows up, but a meter and a preview always show it coming, so it's never a surprise. Classic is endless. The Daily Drop is the same puzzle for everyone, each day. Drag to aim, let go to drop, and collect candy-bright looks for your blocks along the way.</p>
<p>Tumble will be free to play, supported by ads and optional in-app purchases. They aren't switched on yet, and the Daily Drop will never have anything paid in it.</p>
<p>Tumble isn't in the stores yet, and it has no release date.</p>
<p><a class="button" href="{R}tumble/">Visit the Tumble page</a></p>""",
    },
    {
        "slug": "meet-turnstone",
        "title": "Meet Turnstone",
        "tag": "Turnstone", "tag_class": "teal",
        "date": "2026-10-27",
        "thumb_alt": "Otto the octopus grinning on a sunny stone quay, with the harbor town across the water behind him",
        "summary": "Our first game is a cozy, turn-based tile puzzle in a sunny harbor town, starring Otto the octopus.",
        "body": f"""<p class="lead">Turnstone is our first game: a cozy tile puzzle set in a sunny harbor town, starring Otto, a round purple octopus who's never in a hurry, and hopes you won't be either.</p>
<p>Every level is a board of glazed tiles marked with stars, leaves, shells and sails. Tap a tile to flip the path between two matching Twins, and three or more matching tiles clear. It's turn-based and made for one thumb, so it plays just as well on the bus, in line or in bed.</p>
<h2>What we promise</h2>
<ul>
<li>No timers that rush you, and no lives or energy that make you wait.</li>
<li>Every tile carries a symbol, so color is never the only clue.</li>
<li>Nothing you can buy is ever usable in the ranked Daily puzzle, and stars are never sold.</li>
</ul>
<p>Turnstone will be free to play, supported by ads and optional in-app purchases. Neither is switched on in this version.</p>
<p>Turnstone is coming to iOS and Android. It isn't in the stores yet. When it is, the store buttons on this site will start working.</p>
<p><a class="button" href="{R}turnstone/">Visit the Turnstone page</a></p>""",
    },
    {
        "slug": "support-site-live",
        "title": "Our support site is live",
        "tag": "Studio", "tag_class": "ink",
        "date": "2026-10-27",
        "thumb_alt": "The studio cat sitting on the quay at night, with a lighthouse and the lit harbor town behind her",
        "summary": "Help, our games' Terms and Privacy Policies, and how to delete your data, all in one place.",
        "body": f"""<p class="lead">This website is where you can get help with our games and read the documents that come with them.</p>
<ul>
<li><a href="{R}support/">Support</a>: how to reach us, and answers to common questions.</li>
<li><a href="{R}legal/">Legal</a>: every game's Terms of Use and Privacy Policy, word for word as the game shows them.</li>
<li><a href="{R}turnstone/delete-data/">Delete your data</a>: how our games erase everything they keep, from inside the game.</li>
</ul>
<p>The site itself uses no cookies, no analytics and no trackers. We're a small studio and we read every message: {email_link("Hello")}.</p>""",
    },
    {
        "slug": "fair-by-design",
        "title": "Fair by design: no lives, no energy",
        "tag": "Turnstone", "tag_class": "teal",
        "date": "2026-10-27",
        "thumb_alt": "A Turnstone board of glazed tiles: gold stars, green leaves, red shells and blue sails",
        "summary": "Why Turnstone never makes you wait, and why the Daily puzzle is the same for everyone.",
        "body": f"""<p class="lead">We want Turnstone to be a game you can trust with your evening.</p>
<p>So it has no lives and no energy: you can always play another level, and nothing makes you wait. There are no timers either. Every move waits for you.</p>
<p>The Daily puzzle is the same board for everyone, and it's played without Tools, so nothing you can buy helps you on it. Stars, the record of how well you played a level, are never for sale.</p>
<p>Turnstone will be free to play, supported by ads and optional in-app purchases. Neither is switched on in this version, which shows no ads and sells nothing for real money. When they arrive, ads will be optional rewarded ads, they will never appear in the ranked Daily, and a Remove ads purchase will be available. The Terms of Use and Privacy Policy will be updated first, and the game will ask you to accept them again.</p>
<p><a class="button" href="{R}turnstone/">See Turnstone</a></p>""",
    },
]


def news_thumb(n, sizes, eager=False):
    return pic(f"news/{n['slug']}", [600, 1200], sizes, n["thumb_alt"], 1200, 900, cls="thumb-img", eager=eager)


def news_cards(items, heading_level=3):
    cards = []
    for n in items:
        cards.append(f"""<li class="news-card">
<div class="news-thumb">{news_thumb(n, "(min-width: 1100px) 300px, (min-width: 640px) 45vw, 92vw")}</div>
<div class="news-body">
<span class="tag {n['tag_class']}">{esc(n['tag'])}</span>
<h{heading_level} class="news-title"><a href="{R}news/{n['slug']}/">{esc(n['title'])}</a></h{heading_level}>
<p class="news-date"><time datetime="{n['date']}">{nice_date(n['date'])}</time></p>
</div>
</li>""")
    return '<ul class="news-grid">\n' + "\n".join(cards) + "\n</ul>"


# ---------------------------------------------------------------- pages

def build_home():
    body = f"""<section class="hero" aria-labelledby="studio-name">
<picture class="hero-art">
<source media="(max-width: 1099px)" type="image/webp" srcset="{R}assets/img/home/hero-tall-450.webp 450w, {R}assets/img/home/hero-tall-900.webp 900w" sizes="100vw">
<source media="(max-width: 1099px)" srcset="{R}assets/img/home/hero-tall-900.jpg 900w" sizes="100vw">
<source type="image/webp" srcset="{R}assets/img/home/hero-wide-1200.webp 1200w, {R}assets/img/home/hero-wide-1800.webp 1800w, {R}assets/img/home/hero-wide-2400.webp 2400w" sizes="100vw">
<img src="{R}assets/img/home/hero-wide-1200.jpg" srcset="{R}assets/img/home/hero-wide-1200.jpg 1200w, {R}assets/img/home/hero-wide-1800.jpg 1800w" sizes="100vw" width="2400" height="1200" alt="Otto the octopus and a phone showing Tumble, side by side on a sunny stone quay at golden hour, with the studio cat sitting between them and a harbor town behind" fetchpriority="high" decoding="async">
</picture>
<div class="hero-copy">
<h1 id="studio-name" class="toy-title">Jarvis Studios</h1>
<p class="hero-line">Playful games for one thumb. Makers of Turnstone and Tumble.</p>
<p><a class="button button-big" href="#our-games">Meet our games</a></p>
</div>
</section>

<section class="section-pad news-section" aria-labelledby="news-h">
<div class="wrap">
<div class="section-head">
<h2 id="news-h">News</h2>
<a class="button button-quiet" href="{R}news/">All news</a>
</div>
{news_cards(NEWS)}
</div>
</section>

<div id="our-games" class="bands" tabindex="-1">
<section class="band band-turnstone" aria-labelledby="band-ts">
<div class="wrap band-grid">
<div class="band-art">
<div class="art-panel">{pic("turnstone/harbor-noon", [800, 1400], "(min-width: 900px) 560px, 92vw", "", 1400, 817, cls="panel-img")}</div>
{otto()}
</div>
<div class="band-copy">
<p class="eyebrow">Tile puzzle · Coming to iOS and Android</p>
<h2 id="band-ts" class="toy-title small">Turnstone</h2>
<p class="band-line">Flip the path between matching Twins, clear the tiles and help Otto brighten his sunny harbor town, one calm tap at a time.</p>
<p><a class="button" href="{R}turnstone/">Discover Turnstone</a></p>
</div>
</div>
</section>

<section class="band band-tumble" aria-labelledby="band-tb">
<div class="wrap band-grid flip">
<div class="band-art">
<div class="art-panel">{pic("tumble/panel", [800, 1400], "(min-width: 900px) 560px, 92vw", "Two phones showing Tumble: the Home screen with its candy-colored logo, and a board where two giant blocks make a Tumble", 1400, 817, cls="panel-img")}</div>
</div>
<div class="band-copy">
<p class="eyebrow">Block puzzle · In development</p>
<h2 id="band-tb" class="toy-title small">Tumble</h2>
<p class="band-line">Drop the pieces, fuse two of a size into a bigger one and chain your way to a Tumble. Drag to aim, let go to drop.</p>
<p><a class="button" href="{R}tumble/">Discover Tumble</a></p>
</div>
</div>
</section>
</div>

<section class="section-pad promise" aria-labelledby="promise-h">
<div class="wrap">
<div class="promise-card">
{cat("look", "cat-peek")}
<h2 id="promise-h">Made to be kind to your time</h2>
<ul class="promise-list">
<li><strong>One thumb, portrait</strong>Made for a phone in one hand. Turnstone is turn-based, so nothing runs while you think.</li>
<li><strong>No lives, no energy</strong>You can always play another round. Nothing makes you wait.</li>
<li><strong>Fair, always</strong>Nothing you can buy wins for you, and nothing paid ever touches the ranked Daily.</li>
</ul>
<p class="promise-note">Our games are free to play, supported by ads and optional in-app purchases, which aren’t switched on yet.</p>
<p><a class="text-link" href="{R}about/">About the studio</a></p>
</div>
</div>
</section>"""
    page("", STUDIO, f"{STUDIO} makes hand-made games for one thumb. Home of Turnstone and Tumble.", "home", body,
         wide=True, body_class="home")


def game_cards():
    return f"""<ul class="game-cards">
<li class="game-card ts">
<div class="gc-art">{pic("turnstone/harbor-noon", [800], "(min-width: 900px) 520px, 92vw", "", 1400, 817, cls="panel-img")}{otto(cls="gc-char", sizes="220px")}</div>
<div class="gc-body">
<span class="tag teal">Coming to iOS and Android</span>
<h2><a href="{R}turnstone/">Turnstone</a></h2>
<p>A cozy, turn-based tile puzzle in a sunny harbor, played with one thumb. No timers, no lives and no energy.</p>
</div>
</li>
<li class="game-card tb">
<div class="gc-art">{pic("tumble/panel", [800], "(min-width: 900px) 520px, 92vw", "", 1400, 817, cls="panel-img")}</div>
<div class="gc-body">
<span class="tag grape">In development</span>
<h2><a href="{R}tumble/">Tumble</a></h2>
<p>A bright drop-and-fuse block puzzle for one thumb. Fuse matching pieces into bigger ones, chain them and clear the rows, in Classic or the Daily Drop.</p>
</div>
</li>
</ul>"""


def build_games():
    body = f"""<h1>Games</h1>
<p class="lead">Two games so far, both made for one thumb and a few spare minutes.</p>
<div class="section">
{game_cards()}
</div>"""
    page("games/", "Games", f"Games by {STUDIO}: Turnstone and Tumble.", "games", body, crumbs=[("Home", ""), ("Games", None)])


SHOTS = [
    ("home", "Home", "The Home screen: Otto floats in the harbor in front of the town, with a big PLAY button for Level 41 and buttons for Community, Open Tide, the Daily Tile and a Tide Jar."),
    ("level", "A level", "A level in progress: a board of glazed tiles marked with stars, leaves, shells and sails, the goals and 13 moves left at the top, and Otto watching from the quay."),
    ("level-cleared", "Level cleared", "The Level Cleared card: two gold stars, a basket of shells and +23 Shells earned, with a Continue button."),
    ("harbor-jar", "A Harbor Jar", "Opening a Harbor Jar at sunset: Otto grins beside the jar and a big shell shows +70 Shells."),
    ("tide-race", "Tide Race", "The Tide Race: five club sailboats race across the harbor toward a finish line, with standings marked on the water."),
    ("profile", "Profile", "The Profile page under a painted night harbor: Otto's portrait on a pedestal with the harbor rank and a showcase for badges."),
]


def build_turnstone():
    shot_html = "\n".join(
        f'<li><a class="shot" href="{R}assets/img/turnstone/shot-{n}-780.jpg" data-lightbox data-caption="{esc(cap)}">'
        f'{pic("turnstone/shot-" + n, [390, 780], "(min-width: 1100px) 170px, (min-width: 700px) 30vw, 58vw", alt, 390, 844, fallback_w=390)}'
        f'<span class="shot-cap">{cap}</span></a></li>' for n, cap, alt in SHOTS)
    features = [
        ("One thumb, taps only", "Portrait and turn-based. No timer runs while you think.", "tap"),
        ("No lives, no energy", "You can always play another level. Nothing makes you wait.", "heart"),
        ("Every tile has a symbol", "Stars, leaves, shells and sails, so color is never the only clue.", "star"),
        ("A fair Daily", "The same puzzle for everyone, played without Tools. Stars are never sold.", "sun"),
        ("Plays offline", "This version keeps your progress on your device and needs no account.", "wave"),
        ("Free to play", "Supported by ads and optional in-app purchases, which aren't switched on yet. Never in the ranked Daily.", "shell"),
    ]
    feat_html = "\n".join(f'<li class="feat feat-{i}"><span class="feat-dot" aria-hidden="true"></span><strong>{t}</strong><span>{d}</span></li>' for t, d, i in features)
    body = f"""<section class="game-hero ts-hero" aria-labelledby="ts-title">
{pic("turnstone/hero-harbor", [900, 1536], "100vw", "", 1536, 640, cls="game-hero-bg", eager=True, fallback_w=900, img_attrs="")}
<div class="wrap game-hero-inner">
<div class="game-hero-copy">
<h1 id="ts-title" class="toy-title">Turnstone</h1>
<p class="hero-line">A cozy tile puzzle for one thumb, starring Otto the octopus.</p>
{store_badges("turnstone")}
</div>
{otto(cls="game-hero-char", sizes="(min-width: 900px) 360px, 50vw")}
</div>
</section>

<div class="wrap">
<div class="crumb-wrap"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="{{home}}">Home</a></li><li><a href="{R}games/">Games</a></li><li aria-current="page">Turnstone</li></ol></nav></div>
<section class="section intro-split" aria-labelledby="about-ts">
<div>
<h2 id="about-ts">About the game</h2>
<p class="lead">{TS_PITCH}</p>
<p>Play the campaign through the harbor, try the Daily puzzle that’s the same for everyone, and build your own levels in the level maker.</p>
</div>
</section>

<section class="section" aria-labelledby="features">
<h2 id="features">Good to know</h2>
<ul class="features">
{feat_html}
</ul>
</section>

<section class="section" aria-labelledby="shots">
<h2 id="shots">Screenshots</h2>
<ul class="shots">
{shot_html}
</ul>
<p class="muted small">Screenshots from a test build. The names and numbers are made-up examples.</p>
</section>

<section class="section video-split" aria-labelledby="see-it">
<div class="phone">
<video controls muted playsinline preload="none" width="390" height="844" poster="{R}assets/media/turnstone-gameplay-poster.jpg" aria-describedby="video-desc">
<source src="{R}assets/media/turnstone-gameplay.mp4" type="video/mp4">
</video>
</div>
<div>
<h2 id="see-it">See it move</h2>
<p id="video-desc">Four seconds of play from a test build, with no sound: a big clear of red shells, then a chain of special tiles that sweeps the whole board.</p>
<p class="muted small">The video does not play by itself. Press play to watch it.</p>
</div>
</section>

<section class="section" aria-labelledby="docs">
<h2 id="docs">Documents and support</h2>
{turnstone_docs_list()}
</section>
</div>"""
    page("turnstone/", "Turnstone", "Turnstone is a cozy, one-thumb, turn-based tile puzzle starring Otto the octopus. Coming soon to iOS and Android.",
         "games", body, wide=True)


def build_legal_doc(game, path, name, short, meta, blocks, other):
    gname = GAMES[game]["name"]
    v, d = meta["version"], meta["effective_date"]
    oth_path, oth_name = other
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">{gname}</p>
<h1>{name}</h1>
{stamp(v, d)}
</header>
<p class="muted">This is the exact text of version {v}, the version the game shows in Settings, under About. See also the <a href="{R}{oth_path}">{oth_name}</a>.</p>
<div class="legal-doc" data-legal-source="content/{game}/{short}.txt" data-version="{v}" data-effective-date="{d}">
{legal_html(blocks)}
</div>
</article>"""
    page(path, f"{name} · {gname}", f"{gname} {name}, version {v}, effective {nice_date(d)}.", "legal", body,
         crumbs=[("Home", ""), ("Legal", "legal/"), (gname, f"{game}/"), (name, None)])


def build_delete_data():
    pv, pd = TS_PRIV_META["version"], TS_PRIV_META["effective_date"]
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">Turnstone</p>
<h1>Delete your Turnstone data</h1>
{stamp(SUPPORT_VERSION, PAGE_DATE, "Page version")}
</header>
<p class="lead">Turnstone can erase everything it keeps about you, from inside the game, at any time. You don't need to contact us, and there's no account to close.</p>
<p>This version of Turnstone keeps all of its data on your device and sends none of it to us (see section 6 of the <a href="{R}turnstone/privacy/">Privacy Policy</a>, version {pv}, effective {nice_date(pd)}). That’s why deleting happens on the device.</p>

<h2 id="steps">How to delete it in the game</h2>
<ol class="steps">
<li>Open <span class="ui-label">Settings</span> (from the menu on Home, or from the Pause menu during a level).</li>
<li>In the <span class="ui-label">Account and social</span> section, tap <span class="ui-label">Delete my data</span> (“Erase everything Turnstone keeps about you.”).</li>
<li>The game lists what will be erased from the device:
<ul>
<li>Your progress: levels, stars, Daily and Tide results</li>
<li>Shells, Tools, Tide Jars and cosmetics</li>
<li>Your name, age group and Terms acceptance</li>
<li>Settings, quests, achievements and stats</li>
<li>Level drafts and boards you made on this device</li>
</ul>
It also says: “This version of Turnstone has no online account. Everything it keeps is on this device, so nothing is stored on a server.” and “This cannot be undone. Afterwards Turnstone starts again from the first level.” Tap <span class="ui-label">Delete my data</span> to go on, or <span class="ui-label">Keep my data</span> to leave.</li>
<li>The game asks “Are you sure?” Tap <span class="ui-label">Yes, delete everything</span>, or <span class="ui-label">Cancel</span>.</li>
<li>The game shows “Turnstone has erased its data from this device.” and “There was no online account to delete.”
<ul>
<li>On Android, tap <span class="ui-label">Close Turnstone</span>.</li>
<li>On iPhone and iPad, close it yourself: swipe up from the bottom edge and swipe Turnstone away.</li>
</ul></li>
<li>The next time you open Turnstone, it starts fresh, as if it were newly installed: it asks your age, shows the Terms, and begins at the first level.</li>
</ol>

<h2 id="if-it-fails">If something could not be erased</h2>
<p>If the game says “Some files could not be erased.”, tap <span class="ui-label">Try again</span>. If it keeps failing, uninstalling Turnstone removes them.</p>

<h2 id="other-ways">Other ways your data is removed</h2>
<ul>
<li>Uninstalling the game also removes its data from your device.</li>
<li>Your device’s own backups (for example, a phone backup you made) may keep a copy until they’re replaced.</li>
<li>Because this version has no account and stores nothing with us, there’s nothing on our side to delete.</li>
</ul>

<h2 id="parents">For parents and guardians</h2>
<p>You can erase everything the game keeps by using “Delete my data” in Settings on your child’s device.</p>

<h2 id="questions">Questions</h2>
<p>Email {email_link("Turnstone data deletion")}. If you’ve written to us and want that email erased, write to the same address. When a later version adds an online account, this page and the Privacy Policy will be updated to explain how deleting the account works.</p>
</article>"""
    page("turnstone/delete-data/", "Delete your data · Turnstone",
         "How to delete everything Turnstone keeps about you, using Delete my data in the game's Settings.", "legal", body,
         crumbs=[("Home", ""), ("Legal", "legal/"), ("Turnstone", "turnstone/"), ("Delete your data", None)])


def turnstone_faq():
    return f"""<div class="faq">
<details open>
<summary>How do I delete my data?</summary>
<div><p>In the game: <span class="ui-label">Settings</span> › <span class="ui-label">Account and social</span> › <span class="ui-label">Delete my data</span>, then confirm with <span class="ui-label">Yes, delete everything</span>. Turnstone erases everything it keeps on your device and starts fresh the next time you open it. The full steps are on <a href="{R}turnstone/delete-data/">Delete your data</a>.</p></div>
</details>
<details>
<summary>How do I contact you?</summary>
<div><p>Email {email_link("Turnstone support")}. You can also find the address inside the game: <span class="ui-label">Settings</span> › <span class="ui-label">About</span> › <span class="ui-label">Contact us</span>.</p></div>
</details>
<details>
<summary>Do I need an account or the internet?</summary>
<div><p>No. This version works offline and has no account. On Android it doesn’t even ask for internet access.</p></div>
</details>
<details>
<summary>I got a new phone, or lost my progress. Can you restore it?</summary>
<div><p>This version keeps your progress only on your device and never sends it to us, so we have no copy to restore, and there’s no cloud save yet. A backup you made of your device may still have one.</p></div>
</details>
<details>
<summary>Are there ads or purchases?</summary>
<div><p>Turnstone will be free to play, supported by ads and optional in-app purchases. This version shows no ads and sells nothing for real money. When they arrive, ads will be optional rewarded ads, they will never appear in the ranked Daily, and a Remove ads purchase will be available. The Terms of Use and Privacy Policy will be updated first, and the game will ask you to accept them again.</p></div>
</details>
<details>
<summary>Why does the game ask my age?</summary>
<div><p>Just once, the first time you open it, so it can set itself up for you. For example, players under 13 pick their name from a list instead of typing one. It keeps only an age group, never your birthday or exact age. See section 5 of the <a href="{R}turnstone/privacy/">Privacy Policy</a>.</p></div>
</details>
<details>
<summary>Where can I get Turnstone?</summary>
<div><p>Turnstone is coming to iOS and Android. It isn’t in the stores yet.</p></div>
</details>
</div>"""


def build_turnstone_support():
    body = f"""<article>
<header class="doc-header prose">
<p class="eyebrow">Turnstone</p>
<h1>Turnstone support</h1>
{stamp(SUPPORT_VERSION, PAGE_DATE, "Page version")}
</header>
<p class="lead">Need help with Turnstone? Email us and we’ll get back to you.</p>
<p class="email-line">{email_link("Turnstone support")}</p>
<p class="muted">It helps to tell us your device (for example, the phone model) and what happened.</p>
<h2>Questions</h2>
{turnstone_faq()}
<h2 class="section">Documents</h2>
{turnstone_docs_list()}
</article>"""
    page("turnstone/support/", "Support · Turnstone", "Help with Turnstone: contact, deleting your data, and common questions.", "support", body,
         crumbs=[("Home", ""), ("Support", "support/"), ("Turnstone", None)])


def build_support():
    body = f"""<h1>Support</h1>
<p class="lead">We’re a small studio and we read every message.</p>
<div class="note">
<h2 id="contact">Contact</h2>
<p class="email-line">{email_link(STUDIO + " support")}</p>
<p>Please tell us which game you’re writing about and which device you play on.</p>
</div>
<section class="section" aria-labelledby="ts-faq">
<h2 id="ts-faq">Turnstone</h2>
{turnstone_faq()}
<p><a href="{R}turnstone/support/">All Turnstone support</a> · <a href="{R}turnstone/delete-data/">Delete your Turnstone data</a></p>
</section>
<section class="section" aria-labelledby="tb-faq">
<h2 id="tb-faq">Tumble</h2>
{tumble_faq()}
<p><a href="{R}tumble/support/">All Tumble support</a> · <a href="{R}tumble/delete-data/">Delete your Tumble data</a></p>
</section>"""
    page("support/", "Support", f"Contact {STUDIO} and get help with our games, including how to delete your data.", "support", body,
         crumbs=[("Home", ""), ("Support", None)])


def build_legal_index():
    body = f"""<h1>Legal</h1>
<p class="lead">The Terms of Use and Privacy Policy for each of our games, and how to delete your data. Our games are free to play, supported by ads and optional in-app purchases; each game’s own documents have the details.</p>
<section class="section" aria-labelledby="ts-docs">
<h2 id="ts-docs"><a href="{R}turnstone/">Turnstone</a></h2>
{turnstone_docs_list()}
</section>
<section class="section" aria-labelledby="tb-docs">
<h2 id="tb-docs"><a href="{R}tumble/">Tumble</a></h2>
{tumble_docs_list()}
</section>
<section class="section prose" aria-labelledby="this-website">
<h2 id="this-website">This website</h2>
<p>This website uses no cookies, no analytics, no advertising and no trackers, and it has no forms. It stores nothing in your browser.</p>
<p>Its fonts (Grandstander, Fredoka and Ultra) load from Google Fonts, so your browser asks Google’s servers for them, as it does on any site that uses them. The site is hosted on GitHub Pages, and GitHub may keep basic logs of visits, such as IP addresses, under its own privacy statement. We don’t receive or use those logs.</p>
<p>If you email us, we use your message and email address only to answer you.</p>
<p>See also the <a href="{R}accessibility/">accessibility statement</a>.</p>
</section>"""
    page("legal/", "Legal", f"Terms of Use, Privacy Policies and data deletion for every {STUDIO} game.", "legal", body,
         crumbs=[("Home", ""), ("Legal", None)])


TB_SHOTS = [
    ("home", "Home", "Tumble's Home screen: the candy-colored logo, a big Play button, your best score and a Daily Drop card, with Shop, News, Stats and Settings along the top."),
    ("run", "A run", "A run in progress: a green piece about to drop into the well, a pink row and a few blocks stacked at the bottom, with Hold and Next above and Rotate and Drop below."),
    ("tumble", "A Tumble", "Two giant yellow blocks fused into a Tumble, with a burst of light and +2,000 points."),
    ("meter", "The floor meter", "A row of dots under the well fills up to show when the rising floor will push the rows up."),
    ("ready", "You’re ready", "The last card of the tutorial: three gold stars and “You’re ready”, with Play and Home buttons."),
    ("daily", "Daily Drop", "The Daily Drop card: today's pieces, a five-day streak, your attempt and a note that it's the same puzzle for everyone, with nothing paid."),
    ("looks", "Looks", "The Looks tab of the Shop: block styles called Jelly, Hard Candy, Glass, Gem, Pixel and Neon."),
    ("shop", "The Shop", "The Shop: a coin counter, the Neon block look in a golden frame, and tabs for Blocks, Boards, Homes, Effects and Sounds."),
]


def build_tumble():
    shot_html = "\n".join(
        f'<li><a class="shot" href="{R}assets/img/tumble/shot-{n}-780.jpg" data-lightbox data-caption="{esc(alt)}">'
        f'{pic("tumble/shot-" + n, [390, 780], "(min-width: 1100px) 170px, (min-width: 700px) 30vw, 58vw", alt, 390, 844, fallback_w=390)}'
        f'<span class="shot-cap">{cap}</span></a></li>' for n, cap, alt in TB_SHOTS)
    features = [
        ("One thumb, drag and drop", "Drag to aim, let go to drop. Portrait, and playable with one hand.", "tap"),
        ("Fuse and chain", "Two pieces of the same size fuse into a bigger one. Fused pieces can chain.", "star"),
        ("Never a surprise", "A rising floor pushes the rows up, and a meter and a preview show it coming.", "sun"),
        ("Classic and Daily Drop", "Classic is endless. The Daily Drop is the same puzzle for everyone, with nothing paid.", "heart"),
        ("Looks to collect", "Bright candy blocks, boards and effects. Coins buy looks, never a win.", "shell"),
        ("Free to play", "Supported by ads and optional in-app purchases, which aren't switched on yet. Never in the ranked Daily.", "wave"),
    ]
    feat_html = "\n".join(f'<li class="feat feat-{i}"><span class="feat-dot" aria-hidden="true"></span><strong>{t}</strong><span>{d}</span></li>' for t, d, i in features)
    body = f"""<section class="tb-hero" aria-labelledby="tb-title">
<div class="wrap tb-hero-grid">
<div class="tb-hero-copy">
<h1 id="tb-title" class="toy-title">Tumble</h1>
<p class="hero-line">A drop-and-fuse block puzzle for one thumb. Fuse, chain and clear.</p>
{store_badges("tumble")}
</div>
<div class="tb-hero-art">{tumble_icon()}</div>
</div>
</section>

<div class="wrap">
<div class="crumb-wrap"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="{{home}}">Home</a></li><li><a href="{R}games/">Games</a></li><li aria-current="page">Tumble</li></ol></nav></div>
<section class="section intro-split" aria-labelledby="about-tb">
<div>
<h2 id="about-tb">About the game</h2>
<p class="lead">{TB_PITCH}</p>
<p>A rising floor slowly pushes the rows up, but a meter and a preview always show it coming, so it's never a surprise. Each size of piece is a tier, so the bigger the piece, the higher the tier.</p>
<p>Classic is endless: play until the well fills. The Daily Drop is the same puzzle for everyone, each day. Drag to aim, let go to drop, and collect bright candy looks for your blocks along the way.</p>
</div>
</section>

<section class="section" aria-labelledby="features">
<h2 id="features">Good to know</h2>
<ul class="features">
{feat_html}
</ul>
<p class="muted ads-note">{ADS_LINE} {ADS_DETAIL}</p>
</section>

<section class="section" aria-labelledby="shots">
<h2 id="shots">Screenshots</h2>
<ul class="shots shots-8">
{shot_html}
</ul>
<p class="muted small">The scores and coin counts in these screenshots are examples.</p>
</section>

<section class="section" aria-labelledby="docs">
<h2 id="docs">Documents and support</h2>
{tumble_docs_list()}
</section>
</div>"""
    page("tumble/", "Tumble", "Tumble is a one-thumb, drop-and-fuse block puzzle: fuse matching pieces, chain them and clear rows. Coming soon to iOS and Android.",
         "games", body, wide=True)


def build_tumble_delete_data():
    pv, pd = TB_PRIV_META["version"], TB_PRIV_META["effective_date"]
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">Tumble</p>
<h1>Delete your Tumble data</h1>
{stamp(SUPPORT_VERSION, PAGE_DATE, "Page version")}
</header>
<p class="lead">Tumble can erase everything it keeps about you, from inside the game, at any time. You don't need to contact us, and there's no account to close.</p>
<p>This version of Tumble keeps all of its data on your device and sends none of it to us (see section 7 of the <a href="{R}tumble/privacy/">Privacy Policy</a>, version {pv}, effective {nice_date(pd)}). That’s why deleting happens on the device.</p>

<h2 id="steps">How to delete it in the game</h2>
<ol class="steps">
<li>Open <span class="ui-label">Settings</span> from the Home screen.</li>
<li>In the <span class="ui-label">Account</span> section, tap <span class="ui-label">Delete my data</span> (“Erase everything Tumble keeps about you.”).</li>
<li>The game lists what will be erased from the device:
<ul>
<li>Your age group and Terms acceptance</li>
<li>Your settings</li>
<li>Your saved run, your run history, your tutorial progress and your Daily Drop record</li>
<li>Your coins and the looks you own</li>
<li>Your ads and purchases file (Remove ads, ad counters)</li>
</ul>
It also says “This cannot be undone. Afterwards Tumble starts again as if it was just installed.” Tap <span class="ui-label">Delete my data</span> to go on, or <span class="ui-label">Keep my data</span> to leave.</li>
<li>The game asks “Are you sure?” Tap <span class="ui-label">Yes, delete everything</span>, or <span class="ui-label">Cancel</span>.</li>
<li>The game shows “Tumble has erased its data from this device.” and “There was no online account to delete.”
<ul>
<li>On Android, tap <span class="ui-label">Close Tumble</span>.</li>
<li>On iPhone and iPad, close it yourself: swipe up from the bottom edge and swipe Tumble away.</li>
</ul></li>
<li>The next time you open Tumble, it starts fresh, as if it were newly installed.</li>
</ol>

<h2 id="if-it-fails">If something could not be erased</h2>
<p>If the game says “Some files could not be erased.”, tap <span class="ui-label">Try again</span>. If it keeps failing, uninstalling Tumble removes them.</p>

<h2 id="other-ways">Other ways your data is removed</h2>
<ul>
<li>Uninstalling the game also removes its data from your device.</li>
<li>Your device’s own backups (for example, a phone backup you made) may keep a copy until they’re replaced.</li>
<li>Deleting your data doesn’t undo a purchase. Apple or Google keep their own record of what you bought, and Restore purchases can give you Remove ads again. It can’t bring back coins you’ve already spent or lost.</li>
<li>Because this version has no account and stores nothing with us, there’s nothing on our side to delete.</li>
</ul>

<h2 id="parents">For parents and guardians</h2>
<p>You can erase everything the game keeps by using “Delete my data” in Settings on your child’s device.</p>

<h2 id="questions">Questions</h2>
<p>Email {email_link("Tumble data deletion")}. If you’ve written to us and want that email erased, write to the same address. When a later version adds an online account, this page and the Privacy Policy will be updated to explain how deleting the account works.</p>
</article>"""
    page("tumble/delete-data/", "Delete your data · Tumble",
         "How to delete everything Tumble keeps about you, using Delete my data in the game's Settings.", "legal", body,
         crumbs=[("Home", ""), ("Legal", "legal/"), ("Tumble", "tumble/"), ("Delete your data", None)])


def tumble_faq():
    return f"""<div class="faq">
<details open>
<summary>How do I play?</summary>
<div><p>Drag across the well to aim the piece, then let go to drop it. The <span class="ui-label">Rotate</span> button turns it, <span class="ui-label">Hold</span> sets one aside for later, and the <span class="ui-label">Drop</span> button works too. When two pieces of the same size touch, they fuse into a bigger one. Full rows clear, and two of the biggest pieces make a Tumble. You can replay the lessons any time from How to play.</p></div>
</details>
<details>
<summary>What is the Daily Drop?</summary>
<div><p>The same puzzle for everyone, each day. Nothing you can buy is usable in it, and ads never appear in it. For now, the online leaderboard isn’t open, so the game shows only your own score, kept on your device.</p></div>
</details>
<details>
<summary>What are coins and looks?</summary>
<div><p>Looks change how Tumble looks and sounds: blocks, boards, effects and more. Coins buy looks only, never a win. Coins have no cash value and can’t be sold or traded.</p></div>
</details>
<details>
<summary>Are there ads? What do Remove ads and Restore purchases do?</summary>
<div><p>Tumble will be free to play, supported by ads and optional in-app purchases. Ads, coin packs and Remove ads aren’t switched on yet. When they are, ads are optional rewarded ads (such as “Keep going” or free coins). We may later add an occasional ad between runs in Classic, which Remove ads would remove. They never appear in the Daily Drop. Players under 13, and anyone whose age group isn’t known, aren’t offered rewarded ads and never see personalized ads.</p>
<p><span class="ui-label">Remove ads</span> takes away the ads you didn’t choose, and the optional ones stay yours to pick. If you bought it before, <span class="ui-label">Restore purchases</span> in Settings gets it back on this device. It can’t bring back coins you’ve already spent or lost.</p></div>
</details>
<details>
<summary>How do I delete my data?</summary>
<div><p>In the game: <span class="ui-label">Settings</span> › <span class="ui-label">Account</span> › <span class="ui-label">Delete my data</span>, then confirm with <span class="ui-label">Yes, delete everything</span>. Tumble erases everything it keeps on your device and starts fresh the next time you open it. The full steps are on <a href="{R}tumble/delete-data/">Delete your data</a>.</p></div>
</details>
<details>
<summary>Do I need an account or the internet?</summary>
<div><p>No. This version works offline and has no account. On Android it doesn’t even ask for internet access.</p></div>
</details>
<details>
<summary>How do I contact you?</summary>
<div><p>Email {email_link("Tumble support")}. You can also find the address inside the game, under <span class="ui-label">Settings</span> › <span class="ui-label">About</span>.</p></div>
</details>
<details>
<summary>Where can I get Tumble?</summary>
<div><p>Tumble is coming soon to iOS and Android. It isn’t in the stores yet.</p></div>
</details>
</div>"""


def build_tumble_support():
    body = f"""<article>
<header class="doc-header prose">
<p class="eyebrow">Tumble</p>
<h1>Tumble support</h1>
{stamp(SUPPORT_VERSION, PAGE_DATE, "Page version")}
</header>
<p class="lead">Need help with Tumble? Email us and we’ll get back to you.</p>
<p class="email-line">{email_link("Tumble support")}</p>
<p class="muted">It helps to tell us your device (for example, the phone model) and what happened.</p>
<h2>Questions</h2>
{tumble_faq()}
<h2 class="section">Documents</h2>
{tumble_docs_list()}
</article>"""
    page("tumble/support/", "Support · Tumble", "Help with Tumble: how to play, the Daily Drop, coins and looks, ads and purchases, deleting your data, and contact.", "support", body,
         crumbs=[("Home", ""), ("Support", "support/"), ("Tumble", None)])


def build_news_index():
    body = f"""<h1>News</h1>
<p class="lead">What we’re making, and what’s new on this site.</p>
<div class="section">
{news_cards(NEWS, heading_level=2)}
</div>"""
    page("news/", "News", f"News from {STUDIO}: Turnstone, Tumble and the studio.", "news", body, crumbs=[("Home", ""), ("News", None)])


def build_news_posts():
    for n in NEWS:
        others = [o for o in NEWS if o["slug"] != n["slug"]][:3]
        body = f"""<article class="post">
<header class="post-header">
<span class="tag {n['tag_class']}">{esc(n['tag'])}</span>
<h1>{esc(n['title'])}</h1>
<p class="news-date"><time datetime="{n['date']}">{nice_date(n['date'])}</time> · {STUDIO}</p>
</header>
<div class="post-thumb">{news_thumb(n, "(min-width: 900px) 820px, 92vw", eager=True)}</div>
<div class="prose post-body">
{n['body']}
</div>
</article>
<section class="section" aria-labelledby="more-news">
<h2 id="more-news">More news</h2>
{news_cards(others)}
</section>"""
        page(f"news/{n['slug']}/", n["title"], n["summary"], "news", body,
             crumbs=[("Home", ""), ("News", "news/"), (n["title"], None)])


def build_about():
    body = f"""<div class="about-head">
<div>
<h1>About the studio</h1>
<p class="lead">{STUDIO} is a small, independent studio that makes hand-made games for phones: warm, readable and played with one thumb.</p>
</div>
{cat("look", "cat-about", "The studio cat, a ginger cat sitting up and looking at you")}
</div>
<section class="section prose" aria-labelledby="what">
<h2 id="what">What we believe</h2>
<p>A good phone game should fit around your day, not the other way around. So our games are built to be read before they’re played: nothing is hidden, and every choice is yours to size up before you make it.</p>
<ul>
<li><strong>Kind to your time.</strong> No lives, no energy, and no timers that make you wait or hurry.</li>
<li><strong>Fair.</strong> Nothing you can buy wins for you, and every ranked Daily is the same for everyone.</li>
<li><strong>Honest about money.</strong> Our games are free to play, supported by ads and optional in-app purchases. They aren’t switched on yet. When they are, ads are mostly optional ones you choose to watch, and they never appear in a ranked Daily.</li>
<li><strong>Readable.</strong> Color is never the only clue, and text sizes can grow.</li>
<li><strong>Private.</strong> We collect as little as we can, and we say exactly what, in plain words.</li>
</ul>
</section>
<section class="section" aria-labelledby="our-games">
<h2 id="our-games">Our games</h2>
{game_cards()}
</section>
<section class="section prose" aria-labelledby="cat-h">
<h2 id="cat-h">And the cat?</h2>
<p>A ginger cat naps on the quay in Turnstone’s harbor. She’s become the studio’s mascot, and she turns up wherever there’s a warm spot to sleep. Look for her around this site, and in our games.</p>
<p>Press and creators: see the <a href="{R}press/">press kit</a>. Everyone else: say hello at {email_link("Hello")}.</p>
</section>"""
    page("about/", "About", f"About {STUDIO}, a small studio making fair, one-thumb games for phones.", "about", body,
         crumbs=[("Home", ""), ("About", None)])


def build_accessibility():
    body = f"""<article class="prose">
<header class="doc-header">
<h1>Accessibility statement</h1>
<ul class="doc-stamp"><li>Page version 1</li><li>Updated <time datetime="{PAGE_DATE}">{nice_date(PAGE_DATE)}</time></li></ul>
</header>
<p class="lead">We want everyone to be able to use this website and play our games. This page says what we do, what we know is not right yet, and how to tell us about a problem.</p>
<h2 id="website">This website</h2>
<p>We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.2 at level AA. We check it ourselves. An outside expert hasn’t audited it.</p>
<ul>
<li>Every page works with a keyboard alone, starts with a “Skip to content” link, and shows a clear outline on the part that has focus.</li>
<li>Text and buttons meet the AA contrast ratios, in both light and dark mode. The site follows your device’s light or dark setting.</li>
<li>Every image has a text description, or is marked as decoration when it adds nothing.</li>
<li>The pages work from 320 pixels wide, and text can be zoomed to 200% without losing content.</li>
<li>If your device asks for reduced motion, the site turns off its small animations. The gameplay video never plays by itself, has no sound, and comes with a written description.</li>
<li>The menus are real buttons with their state announced to screen readers.</li>
</ul>
<h2 id="games">Our games</h2>
<p>Turnstone is turn-based and played with taps only, in portrait, with one thumb. It has no timers. Every tile carries a symbol as well as a color, so color is never the only clue, and the game has a Text size setting (Default, Large and Larger).</p>
<p>Things we know aren’t right yet in Turnstone: there is no high-contrast option, and some screens still label only the selected tab of the main menu. We are working on both.</p>
<h2 id="known">Known limits on this site</h2>
<ul>
<li>Until our games are in the stores, the site says so in plain text instead of showing store badges.</li>
<li>Our legal documents are shown word for word as the games show them, so we cannot shorten or reword them on this site.</li>
</ul>
<h2 id="contact">Tell us about a problem</h2>
<p>If something on this site or in our games is hard to use, email {email_link("Accessibility")}. Please tell us the page or screen, and the device and any assistive technology you use. We aim to reply within five working days.</p>
</article>"""
    page("accessibility/", "Accessibility statement", f"How {STUDIO} makes this website and its games accessible, known limits, and how to report a problem.", "legal", body,
         crumbs=[("Home", ""), ("Legal", "legal/"), ("Accessibility statement", None)])


def build_press():
    downloads = [
        ("Studio wordmark (light background)", "assets/press/jarvis-studios-logo.png", "PNG, 884 × 352"),
        ("Studio wordmark (dark background)", "assets/press/jarvis-studios-logo-on-dark.png", "PNG, 884 × 352, with a light edge"),
        ("Studio key art: Otto and Tumble", "assets/press/jarvis-studios-key-art.jpg", "JPEG, 2400 × 1200"),
        ("Turnstone key art", "assets/press/turnstone-key-art.jpg", "JPEG, 2400 × 1200"),
        ("Otto the octopus", "assets/press/otto.png", "PNG, transparent"),
        ("Tumble app icon", "assets/press/tumble-icon.png", "PNG, 512 × 512"),
    ] + [(f"Turnstone screenshot: {cap}", f"assets/press/turnstone-{n}.jpg", "JPEG, 1170 × 2532") for n, cap, _ in SHOTS
         ] + [(f"Tumble screenshot: {cap}", f"assets/press/tumble-{n}.jpg", "JPEG, 780 × 1688") for n, cap, _ in TB_SHOTS]
    dl = "\n".join(f'<li><a href="{R}{p}" download><span class="doc-name">{esc(t)}</span><span class="doc-meta">{esc(m)}</span></a></li>' for t, p, m in downloads)
    body = f"""<h1>Press kit</h1>
<p class="lead">Facts, art and screenshots for writing about {STUDIO} and our games.</p>
<div class="press-hero">{pic("home/hero-wide", [1200, 1800], "(min-width: 1100px) 1048px, 92vw", "Otto the octopus and a phone showing Tumble on a sunny stone quay, with the studio cat between them", 2400, 1200, cls="panel-img")}</div>
<section class="section" aria-labelledby="facts">
<h2 id="facts">Studio fact sheet</h2>
<dl class="fact-sheet">
<div><dt>Studio</dt><dd>{STUDIO}, an independent game studio</dd></div>
<div><dt>Games</dt><dd><a href="{R}turnstone/">Turnstone</a> (tile puzzle) and <a href="{R}tumble/">Tumble</a> (block puzzle)</dd></div>
<div><dt>Platforms</dt><dd>iOS and Android (Turnstone and Tumble coming soon)</dd></div>
<div><dt>Business model</dt><dd>Free to play, supported by ads and optional in-app purchases. Not switched on yet. Never in a ranked Daily.</dd></div>
<div><dt>Characters</dt><dd>Otto, a round purple octopus (Turnstone), and the studio cat</dd></div>
<div><dt>In one line</dt><dd>Hand-made games for one thumb: portrait, taps or drags only, no lives, no energy, nothing that wins for you.</dd></div>
<div><dt>Press contact</dt><dd>{email_link("Press")}</dd></div>
</dl>
</section>
<section class="section" aria-labelledby="tb-facts">
<h2 id="tb-facts">Tumble fact sheet</h2>
<dl class="fact-sheet">
<div><dt>Game</dt><dd>Tumble, a portrait drop-and-fuse block puzzle</dd></div>
<div><dt>Status</dt><dd>In development. Coming soon to iOS and Android, with no release date yet.</dd></div>
<div><dt>How it works</dt><dd>Tetris-shaped pieces drop into a well. Two pieces of the same size fuse into a bigger one (size is the tier), and fused pieces can chain. Full rows clear, and two of the biggest make a Tumble.</dd></div>
<div><dt>Rising floor</dt><dd>A floor slowly pushes the rows up, with a meter and a preview so it’s never a surprise.</dd></div>
<div><dt>Modes</dt><dd>Classic, which is endless, and the Daily Drop, the same puzzle for everyone each day</dd></div>
<div><dt>Controls</dt><dd>One thumb: drag to aim, let go to drop</dd></div>
<div><dt>Look</dt><dd>Bright candy blocks, with looks to collect</dd></div>
<div><dt>Price</dt><dd>Free to play, supported by ads and optional in-app purchases (optional rewarded ads, possibly an occasional ad between runs in Classic later, never in the ranked Daily, and Remove ads)</dd></div>
<div><dt>Details</dt><dd><a href="{R}tumble/">Game page</a> · <a href="{R}tumble/privacy/">Privacy Policy</a> · <a href="{R}tumble/terms/">Terms of Use</a></dd></div>
</dl>
</section>
<section class="section" aria-labelledby="dl">
<h2 id="dl">Downloads</h2>
<ul class="doc-list">
{dl}
</ul>
<p class="muted small">You may use these images to write about our games. Please don’t change the characters or the wordmark. Turnstone screenshots are from a test build.</p>
</section>"""
    page("press/", "Press kit", f"The {STUDIO} press kit: fact sheets, wordmark, key art and screenshots.", "about", body,
         crumbs=[("Home", ""), ("About", "about/"), ("Press kit", None)])


def build_404():
    """GitHub Pages serves 404.html for a missing address at ANY depth, so relative paths cannot be trusted there. The page carries its
    own styles and art inline, and a small script finds the site root (siteUrl from config.js if set; otherwise it looks for
    site-root.txt in each parent folder of the address) and points <base> at it, which fixes every link on the page."""
    css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    cat_svg = (ROOT / "assets/img/studio/cat-nap.svg").read_text(encoding="utf-8")
    cat_svg = cat_svg.replace("<svg ", '<svg role="img" aria-label="The studio cat, napping" ', 1)
    fav = (ROOT / "favicon.svg").read_text(encoding="utf-8")
    import urllib.parse
    fav_uri = "data:image/svg+xml," + urllib.parse.quote(fav)
    script = """(function () {
  var configured = %s;
  var base = document.getElementById("site-base");
  if (configured) { base.setAttribute("href", configured); return; }
  if (!window.fetch) return;
  var parts = location.pathname.split("/");
  parts.pop();
  var candidates = [];
  while (parts.length) { candidates.push(parts.join("/") + "/"); parts.pop(); }
  (function tryAt(i) {
    if (i >= candidates.length) return;
    fetch(candidates[i] + "site-root.txt", { method: "HEAD", cache: "no-store", credentials: "omit" })
      .then(function (r) { if (r.ok) base.setAttribute("href", candidates[i]); else tryAt(i + 1); })
      .catch(function () { tryAt(i + 1); });
  })(0);
})();""" % json.dumps(SITE_URL)
    nav = "\n".join(f'<li><a class="nav-link" href="{href}">{label}</a></li>' for _, label, href in NAV)
    doc = f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base id="site-base" href="./">
<title>Page not found · {STUDIO}</title>
<meta name="robots" content="noindex">
<link rel="icon" href="{fav_uri}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>
{css}
.not-found svg {{ width: 220px; height: auto; margin: 0 auto 10px; display: block; }}
</style>
<script>
{script}
</script>
</head>
<body>
<a class="skip-link" href="#main" onclick="document.getElementById('main').focus(); return false;">Skip to content</a>
<header class="site-header">
<div class="wrap header-row">
<a class="wordmark" href="./" aria-label="{STUDIO}, home"><span class="wm-top" aria-hidden="true">JARVIS</span><span class="wm-bottom" aria-hidden="true">STUDIOS</span></a>
<nav class="site-nav static" aria-label="Main">
<ul class="nav-list">
{nav}
</ul>
</nav>
</div>
</header>
<main id="main" tabindex="-1">
<div class="wrap not-found">
{cat_svg}
<h1>Page not found</h1>
<p class="lead">The studio cat looked all around the harbor, but there’s no page at this address. She’s gone back to sleep.</p>
<p><a class="button" href="./">Go to the home page</a></p>
<p>Looking for a game’s documents? Try <a href="legal/">Legal</a> or <a href="support/">Support</a>.</p>
</div>
</main>
<footer class="site-footer simple">
<div class="wrap foot-base">
<p>© {YEAR} {STUDIO}. This website uses no cookies, no analytics and no trackers.</p>
</div>
</footer>
</body>
</html>
"""
    (ROOT / "404.html").write_text(doc, encoding="utf-8")


def main():
    build_home()
    build_games()
    build_turnstone()
    build_legal_doc("turnstone", "turnstone/terms/", "Terms of Use", "terms_of_use", TS_TERMS_META, TS_TERMS, ("turnstone/privacy/", "Privacy Policy"))
    build_legal_doc("turnstone", "turnstone/privacy/", "Privacy Policy", "privacy_policy", TS_PRIV_META, TS_PRIV, ("turnstone/terms/", "Terms of Use"))
    build_delete_data()
    build_turnstone_support()
    build_support()
    build_legal_index()
    build_tumble()
    build_legal_doc("tumble", "tumble/terms/", "Terms of Use", "terms_of_use", TB_TERMS_META, TB_TERMS, ("tumble/privacy/", "Privacy Policy"))
    build_legal_doc("tumble", "tumble/privacy/", "Privacy Policy", "privacy_policy", TB_PRIV_META, TB_PRIV, ("tumble/terms/", "Terms of Use"))
    build_tumble_delete_data()
    build_tumble_support()
    build_news_index()
    build_news_posts()
    build_about()
    build_accessibility()
    build_press()
    build_404()
    pages = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    print(f"build: wrote {len(pages)} pages (support email: {EMAIL})")
    for p in pages:
        print("  " + p)


if __name__ == "__main__":
    main()
