#!/usr/bin/env python3
"""Builds every HTML page of the Jarvis Studios website from one layout.

    python3 tools/build.py

The output is plain HTML committed next to this script's folder, so GitHub Pages serves the site as it is (no build runs there).
Run this after changing a page below, the support email in assets/js/config.js, or a legal text in content/.

Rules the output follows (tools/check.py verifies them):
- Every link and asset path is relative (no leading "/"), so the site works both at a domain root
  (https://jarvisstudiohq.github.io/) and under a subpath (https://cjarvis0.github.io/jarvis-studio/).
- Turnstone's legal pages are generated from content/turnstone/*.txt, verbatim copies of the game's own legal files.
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
GAME_LINKS = [("Turnstone", "turnstone/", "Cozy tile puzzle"), ("Hot Crumb", "hot-crumb/", "Bakery card game, in development")]

# Store pages. Leave a URL empty while the game is not in that store: the badge then shows "Coming soon" and is not a link.
GAMES = {
    "turnstone": {"name": "Turnstone", "app_store": "", "google_play": "", "status": "Coming soon to iOS and Android"},
    "hot-crumb": {"name": "Hot Crumb", "app_store": "", "google_play": "", "status": "In development"},
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


def mabel(cls="cutout", alt="Mabel, a badger baker in a tall white chef's hat and a yellow apron, smiling", sizes="(min-width: 900px) 280px, 40vw"):
    return pic("hot-crumb/mabel", [300, 600], sizes, alt, 600, 935, cls=cls, fallback="png", fallback_w=600)


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
<p>Cozy, hand-made games for one thumb.</p>
<p class="foot-email">Support: {email_link()}</p>
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
<li><a href="{rel}turnstone/terms/">Terms of Use</a></li>
<li><a href="{rel}turnstone/privacy/">Privacy Policy</a></li>
<li><a href="{rel}turnstone/delete-data/">Data deletion</a></li>
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

TS_PITCH = ("Turnstone is a cozy tile puzzle set in a sunny harbor town, starring Otto the octopus. It is turn-based and made "
            "for one thumb: tap a tile to flip the path between two matching Twins, and three or more matching tiles clear. "
            "Take your time. There are no timers, no lives and no energy, so you never have to wait or pay to keep playing.")
HC_PITCH = ("Hot Crumb is a cozy bakery card game for one thumb. You are Mabel, a flour-dusted badger who runs a tiny hillside "
            "bakery. Each day you draw a hand of ingredient cards, pick the ones that make a recipe everyone already knows, "
            "and slide the tin into the oven. Before you commit, the counter shows exactly what the bake will score.")

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


def hotcrumb_docs_list(rel_prefix=R):
    rows = [
        ("hot-crumb/terms/", "Terms of Use", "Not yet published"),
        ("hot-crumb/privacy/", "Privacy Policy", "Not yet published"),
        ("hot-crumb/support/", "Support", "Contact"),
    ]
    return '<ul class="doc-list">\n' + "\n".join(
        f'<li><a href="{rel_prefix}{h}"><span class="doc-name">{n}</span><span class="doc-meta">{m}</span></a></li>'
        for h, n, m in rows) + "\n</ul>"


# ---------------------------------------------------------------- news

NEWS = [
    {
        "slug": "meet-turnstone",
        "title": "Meet Turnstone",
        "tag": "Turnstone", "tag_class": "teal",
        "date": "2026-10-27",
        "thumb_alt": "Otto the octopus grinning on a sunny stone quay, with the harbor town across the water behind him",
        "summary": "Our first game is a cozy, turn-based tile puzzle in a sunny harbor town, starring Otto the octopus.",
        "body": f"""<p class="lead">Turnstone is our first game: a cozy tile puzzle set in a sunny harbor town, starring Otto, a round purple octopus who would rather you took your time.</p>
<p>Every level is a board of glazed tiles marked with stars, leaves, shells and sails. Tap a tile to flip the path between two matching Twins, and three or more matching tiles clear. It is turn-based and made for one thumb, so it plays well on a bus, in a queue or in bed.</p>
<h2>What we promise</h2>
<ul>
<li>No timers that rush you, and no lives or energy that make you wait.</li>
<li>Every tile carries a symbol, so color is never the only clue.</li>
<li>Nothing you can buy is ever usable in the ranked Daily puzzle, and stars are never sold.</li>
</ul>
<p>Turnstone is coming to iOS and Android. It is not in the stores yet; when it is, the store buttons on this site will start working.</p>
<p><a class="button" href="{R}turnstone/">Visit the Turnstone page</a></p>""",
    },
    {
        "slug": "hot-crumb-in-the-oven",
        "title": "Hot Crumb is in the oven",
        "tag": "Hot Crumb", "tag_class": "crust",
        "date": "2026-10-27",
        "thumb_alt": "Mabel the badger baker standing in her kitchen in front of a brick oven, with shelves of jars and bowls above",
        "summary": "Our second game is a cozy bakery card game starring Mabel the badger. It is early, and here is what we can share.",
        "body": f"""<p class="lead">Our second game is baking. Hot Crumb is a cozy card game for one thumb, starring Mabel, a flour-dusted badger who runs a tiny hillside bakery.</p>
<p>Each day you draw a hand of ingredient cards, pick the ones that make a recipe everyone already knows, and slide the tin into the oven. Before you commit, the counter shows exactly what the bake will score, so every choice is yours to read.</p>
<p>Hot Crumb is in development. The art you see here is early, and Mabel will get her full set of poses before anything ships. It is not available to download, and it has no release date yet.</p>
<p><a class="button" href="{R}hot-crumb/">Visit the Hot Crumb page</a></p>""",
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
<li><a href="{R}turnstone/delete-data/">Delete your data</a>: how Turnstone erases everything it keeps, from inside the game.</li>
</ul>
<p>The site itself uses no cookies, no analytics and no trackers. We are a small studio and we read every message: {email_link("Hello")}.</p>""",
    },
    {
        "slug": "fair-by-design",
        "title": "Fair by design: no lives, no energy",
        "tag": "Turnstone", "tag_class": "teal",
        "date": "2026-10-27",
        "thumb_alt": "A Turnstone board of glazed tiles: gold stars, green leaves, red shells and blue sails",
        "summary": "Why Turnstone never makes you wait, and why the Daily puzzle is the same for everyone.",
        "body": f"""<p class="lead">We want Turnstone to be a game you can trust with your evening.</p>
<p>So it has no lives and no energy: you can always play another level, and you never have to wait or pay to keep going. There are no timers either. Every move waits for you.</p>
<p>The Daily puzzle is the same board for everyone, and it is played without Tools, so nothing you can buy helps you on it. Stars, the record of how well you played a level, are never for sale.</p>
<p>This version of Turnstone shows no ads and sells nothing for real money. If that ever changes, the Terms of Use and Privacy Policy will be updated first, and the game will ask you to accept them again.</p>
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
<source media="(max-width: 699px)" type="image/webp" srcset="{R}assets/img/home/hero-tall-450.webp 450w, {R}assets/img/home/hero-tall-900.webp 900w" sizes="100vw">
<source media="(max-width: 699px)" srcset="{R}assets/img/home/hero-tall-900.jpg 900w" sizes="100vw">
<source type="image/webp" srcset="{R}assets/img/home/hero-wide-1200.webp 1200w, {R}assets/img/home/hero-wide-1800.webp 1800w, {R}assets/img/home/hero-wide-2400.webp 2400w" sizes="100vw">
<img src="{R}assets/img/home/hero-wide-1200.jpg" srcset="{R}assets/img/home/hero-wide-1200.jpg 1200w, {R}assets/img/home/hero-wide-1800.jpg 1800w" sizes="100vw" width="2400" height="1200" alt="Otto the octopus and Mabel the badger baker side by side on a sunny stone quay at golden hour, with the studio cat sitting between them and a harbor town behind" fetchpriority="high" decoding="async">
</picture>
<div class="hero-copy">
<h1 id="studio-name" class="toy-title">Jarvis Studios</h1>
<p class="hero-line">Cozy games for one thumb. Makers of Turnstone and Hot Crumb.</p>
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

<section class="band band-hotcrumb" aria-labelledby="band-hc">
<div class="wrap band-grid flip">
<div class="band-art">
<div class="art-panel">{pic("hot-crumb/kitchen", [600, 1024], "(min-width: 900px) 480px, 92vw", "", 1024, 1024, cls="panel-img")}</div>
{mabel()}
</div>
<div class="band-copy">
<p class="eyebrow">Bakery card game · In development</p>
<h2 id="band-hc" class="toy-title small">Hot Crumb</h2>
<p class="band-line">Pick the ingredients, bake the recipes everyone loves and see the score before you commit, in Mabel’s tiny hillside bakery.</p>
<p><a class="button" href="{R}hot-crumb/">Peek in the kitchen</a></p>
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
<li><strong>Taps only, one thumb</strong>Portrait, turn-based, and calm. Nothing runs while you think.</li>
<li><strong>No lives, no energy</strong>You never have to wait, or pay, to keep playing.</li>
<li><strong>Fair, always</strong>Nothing you can buy wins for you, and stars are never sold.</li>
</ul>
<p><a class="text-link" href="{R}about/">About the studio</a></p>
</div>
</div>
</section>"""
    page("", STUDIO, f"{STUDIO} makes cozy, hand-made games for one thumb. Home of Turnstone and Hot Crumb.", "home", body,
         wide=True, body_class="home")


def game_cards():
    return f"""<ul class="game-cards">
<li class="game-card ts">
<div class="gc-art">{pic("turnstone/harbor-noon", [800], "(min-width: 900px) 520px, 92vw", "", 1400, 817, cls="panel-img")}{otto(cls="gc-char", sizes="220px")}</div>
<div class="gc-body">
<span class="tag teal">Coming to iOS and Android</span>
<h2><a href="{R}turnstone/">Turnstone</a></h2>
<p>A cozy, turn-based tile puzzle in a sunny harbor, played with one thumb. No timers, no lives, no energy.</p>
</div>
</li>
<li class="game-card hc">
<div class="gc-art">{pic("hot-crumb/kitchen", [600], "(min-width: 900px) 520px, 92vw", "", 1024, 1024, cls="panel-img")}{mabel(cls="gc-char", sizes="180px")}</div>
<div class="gc-body">
<span class="tag crust">In development</span>
<h2><a href="{R}hot-crumb/">Hot Crumb</a></h2>
<p>A cozy bakery card game for one thumb, starring Mabel the badger baker. Pick ingredients, bake recipes everyone knows, and see the score before you commit.</p>
</div>
</li>
</ul>"""


def build_games():
    body = f"""<h1>Games</h1>
<p class="lead">Two games so far, both made for one thumb and a few quiet minutes.</p>
<div class="section">
{game_cards()}
</div>"""
    page("games/", "Games", f"Games by {STUDIO}: Turnstone and Hot Crumb.", "games", body, crumbs=[("Home", ""), ("Games", None)])


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
        ("No lives, no energy", "You never have to wait, or pay, to keep playing.", "heart"),
        ("Every tile has a symbol", "Stars, leaves, shells and sails, so color is never the only clue.", "star"),
        ("A fair Daily", "The same puzzle for everyone, played without Tools. Stars are never sold.", "sun"),
        ("Plays offline", "This version keeps your progress on your device and needs no account.", "wave"),
        ("No ads, nothing for sale", "This version shows no ads and sells nothing for real money.", "shell"),
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
<p>Play the campaign through the harbor, try the Daily puzzle that is the same for everyone, and build your own levels in the level maker.</p>
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
<p class="muted small">Screenshots from a test build. Names and numbers are examples made up by the game.</p>
</section>

<section class="section video-split" aria-labelledby="see-it">
<div class="phone">
<video controls muted playsinline preload="none" width="390" height="844" poster="{R}assets/media/turnstone-gameplay-poster.jpg" aria-describedby="video-desc">
<source src="{R}assets/media/turnstone-gameplay.mp4" type="video/mp4">
</video>
</div>
<div>
<h2 id="see-it">See it move</h2>
<p id="video-desc">Four seconds of play from a test build, without sound: a big clear of red shells, then a chain of special tiles that sweeps the whole board.</p>
<p class="muted small">The video does not play by itself. Press play to watch it.</p>
</div>
</section>

<section class="section" aria-labelledby="docs">
<h2 id="docs">Documents and support</h2>
{turnstone_docs_list()}
</section>
</div>"""
    page("turnstone/", "Turnstone", "Turnstone is a cozy, one-thumb, turn-based tile puzzle starring Otto the octopus. Coming to iOS and Android.",
         "games", body, wide=True)


def build_legal_doc(path, name, short, meta, blocks, other):
    v, d = meta["version"], meta["effective_date"]
    oth_path, oth_name = other
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">Turnstone</p>
<h1>{name}</h1>
{stamp(v, d)}
</header>
<p class="muted">This is the exact text of version {v}, the version the game shows in Settings, under About. See also the <a href="{R}{oth_path}">{oth_name}</a>.</p>
<div class="legal-doc" data-legal-source="content/turnstone/{short}.txt" data-version="{v}" data-effective-date="{d}">
{legal_html(blocks)}
</div>
</article>"""
    page(path, f"{name} · Turnstone", f"Turnstone {name}, version {v}, effective {nice_date(d)}.", "legal", body,
         crumbs=[("Home", ""), ("Legal", "legal/"), ("Turnstone", "turnstone/"), (name, None)])


def build_delete_data():
    pv, pd = TS_PRIV_META["version"], TS_PRIV_META["effective_date"]
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">Turnstone</p>
<h1>Delete your Turnstone data</h1>
{stamp(SUPPORT_VERSION, PAGE_DATE, "Page version")}
</header>
<p class="lead">Turnstone can erase everything it keeps about you, from inside the game, at any time. You do not need to contact us, and there is no account to close.</p>
<p>This version of Turnstone keeps all of its data on your device and sends none of it to us (see section 6 of the <a href="{R}turnstone/privacy/">Privacy Policy</a>, version {pv}, effective {nice_date(pd)}). That is why deleting happens on the device.</p>

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
<li>Your device’s own backups (for example, a phone backup you made) may keep a copy until they are replaced.</li>
<li>Because this version has no account and stores nothing with us, there is nothing on our side to delete.</li>
</ul>

<h2 id="parents">For parents and guardians</h2>
<p>You can erase everything the game keeps by using “Delete my data” in Settings on your child’s device.</p>

<h2 id="questions">Questions</h2>
<p>Email {email_link("Turnstone data deletion")}. If you have written to us and want that email erased, write to the same address. When a later version adds an online account, this page and the Privacy Policy will be updated to explain how deleting the account works.</p>
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
<div><p>No. This version works offline and has no account. On Android it does not even ask for internet access.</p></div>
</details>
<details>
<summary>I got a new phone, or lost my progress. Can you restore it?</summary>
<div><p>This version keeps your progress only on your device and never sends it to us, so we have no copy to restore and there is no cloud save yet. A backup of your device that you made yourself may still hold a copy.</p></div>
</details>
<details>
<summary>Are there ads or purchases?</summary>
<div><p>This version of Turnstone does not sell anything for real money and does not show advertising. If we ever add purchases or ads, the Terms of Use and Privacy Policy will be updated first and the game will ask you to accept them again.</p></div>
</details>
<details>
<summary>Why does the game ask my age?</summary>
<div><p>Once, the first time you open it, so it can set itself up for you. For example, players under 13 pick their name from a list instead of typing one. It keeps only an age group, never your birthday or exact age. See section 5 of the <a href="{R}turnstone/privacy/">Privacy Policy</a>.</p></div>
</details>
<details>
<summary>Where can I get Turnstone?</summary>
<div><p>Turnstone is coming to iOS and Android. It is not in the stores yet.</p></div>
</details>
</div>"""


def build_turnstone_support():
    body = f"""<article>
<header class="doc-header prose">
<p class="eyebrow">Turnstone</p>
<h1>Turnstone support</h1>
{stamp(SUPPORT_VERSION, PAGE_DATE, "Page version")}
</header>
<p class="lead">Need help with Turnstone? Email us and we will get back to you.</p>
<p class="email-line">{email_link("Turnstone support")}</p>
<p class="muted">It helps to tell us your device (for example, the phone model), and what happened.</p>
<h2>Questions</h2>
{turnstone_faq()}
<h2 class="section">Documents</h2>
{turnstone_docs_list()}
</article>"""
    page("turnstone/support/", "Support · Turnstone", "Help with Turnstone: contact, deleting your data, and common questions.", "support", body,
         crumbs=[("Home", ""), ("Support", "support/"), ("Turnstone", None)])


def build_support():
    body = f"""<h1>Support</h1>
<p class="lead">We are a small studio and we read every message.</p>
<div class="note">
<h2 id="contact">Contact</h2>
<p class="email-line">{email_link(STUDIO + " support")}</p>
<p>Please say which game you are writing about and which device you play on.</p>
</div>
<section class="section" aria-labelledby="ts-faq">
<h2 id="ts-faq">Turnstone</h2>
{turnstone_faq()}
<p><a href="{R}turnstone/support/">All Turnstone support</a> · <a href="{R}turnstone/delete-data/">Delete your Turnstone data</a></p>
</section>
<section class="section" aria-labelledby="hc-faq">
<h2 id="hc-faq">Hot Crumb</h2>
<p>Hot Crumb is in development and is not available yet. Questions are welcome at the email above.</p>
</section>"""
    page("support/", "Support", f"Contact {STUDIO} and get help with our games, including how to delete your data.", "support", body,
         crumbs=[("Home", ""), ("Support", None)])


def build_legal_index():
    body = f"""<h1>Legal</h1>
<p class="lead">The Terms of Use and Privacy Policy for each of our games, and how to delete your data.</p>
<section class="section" aria-labelledby="ts-docs">
<h2 id="ts-docs"><a href="{R}turnstone/">Turnstone</a></h2>
{turnstone_docs_list()}
</section>
<section class="section" aria-labelledby="hc-docs">
<h2 id="hc-docs"><a href="{R}hot-crumb/">Hot Crumb</a></h2>
<p class="muted">Hot Crumb is in development. Its documents will be published here before the game is released.</p>
{hotcrumb_docs_list()}
</section>
<section class="section prose" aria-labelledby="this-website">
<h2 id="this-website">This website</h2>
<p>This website uses no cookies, no analytics, no advertising and no trackers, and it has no forms. It stores nothing in your browser.</p>
<p>Its fonts (Grandstander, Fredoka and Ultra) are loaded from Google Fonts, so your browser asks Google’s servers for them, as it does on any site that uses Google Fonts. The site is hosted on GitHub Pages, and GitHub may keep basic logs of visits, such as IP addresses, under its own privacy statement. We do not receive or use those logs.</p>
<p>If you email us, we use your message and email address only to answer you.</p>
<p>See also the <a href="{R}accessibility/">accessibility statement</a>.</p>
</section>"""
    page("legal/", "Legal", f"Terms of Use, Privacy Policies and data deletion for every {STUDIO} game.", "legal", body,
         crumbs=[("Home", ""), ("Legal", None)])


def build_hot_crumb():
    steps = [
        ("flour", "Draw a hand", "Each day starts with a hand of ingredient cards: flour, eggs, butter, sugar, fruit and cream."),
        ("egg", "Pick a recipe", "Choose the cards that make a recipe everyone already knows. The counter shows the score before you bake."),
        ("butter", "Into the oven", "Slide the tin in, please the picky village Regulars, and save up for the Royal Tasting."),
    ]
    steps_html = "\n".join(
        f'<li class="hc-step"><span class="hc-icon">{pic("hot-crumb/icon-" + ic, [128], "64px", "", 128, 128, fallback="png", fallback_w=128)}</span><strong>{t}</strong><span>{d}</span></li>'
        for ic, t, d in steps)
    body = f"""<section class="hc-hero" aria-labelledby="hc-title">
<div class="wrap hc-hero-grid">
<div class="hc-hero-copy">
<span class="tag crust">In development</span>
<h1 id="hc-title" class="toy-title crust">Hot Crumb</h1>
<p class="hero-line">A cozy bakery card game for one thumb, starring Mabel the badger baker.</p>
<p class="muted">by {STUDIO}. Not yet available, and no release date yet.</p>
</div>
<div class="hc-hero-art">
<div class="art-panel">{pic("hot-crumb/kitchen", [600, 1024], "(min-width: 900px) 480px, 92vw", "Mabel's bakery kitchen: a brick oven in an arch, shelves of jars and bowls, copper pans and a window onto the hills", 1024, 1024, cls="panel-img", eager=True, fallback_w=600)}</div>
{mabel(sizes="(min-width: 900px) 260px, 38vw")}
</div>
</div>
</section>

<div class="wrap">
<div class="crumb-wrap"><nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="{{home}}">Home</a></li><li><a href="{R}games/">Games</a></li><li aria-current="page">Hot Crumb</li></ol></nav></div>
<section class="section" aria-labelledby="pitch">
<h2 id="pitch">The pitch</h2>
<p class="lead">{HC_PITCH}</p>
<p class="prose">Hold your Flour back and it rises, so tomorrow’s bake is bigger, if you can afford to wait. Please the picky village Regulars, spend coins at the Market on better ingredients and charming Kitchen Helpers that bend the rules, and get through a week of rising targets to win the Royal Tasting. A run takes 15 to 20 minutes, and you can pause after any bake.</p>
</section>
<section class="section" aria-labelledby="how">
<h2 id="how">A day in the bakery</h2>
<ol class="hc-steps">
{steps_html}
</ol>
</section>
<section class="section" aria-labelledby="hc-facts">
<h2 id="hc-facts">Good to know</h2>
<ul class="features">
<li class="feat feat-tap"><span class="feat-dot" aria-hidden="true"></span><strong>One thumb, taps only</strong><span>Portrait and turn-based. No timer runs while you think.</span></li>
<li class="feat feat-star"><span class="feat-dot" aria-hidden="true"></span><strong>Readable before you bake</strong><span>Flavor × Warmth = Delight, shown in full before you tap Bake.</span></li>
<li class="feat feat-heart"><span class="feat-dot" aria-hidden="true"></span><strong>Fair, always</strong><span>No energy, no lives, and nothing paid touches a run.</span></li>
</ul>
<p class="muted small">The art on this page is early work in progress.</p>
</section>
<section class="section" aria-labelledby="hc-docs">
<h2 id="hc-docs">Documents</h2>
<p class="muted">Hot Crumb has no Terms of Use or Privacy Policy yet. They will be published here before the game is released.</p>
{hotcrumb_docs_list()}
</section>
</div>"""
    page("hot-crumb/", "Hot Crumb", "Hot Crumb is a cozy bakery card game for one thumb by Jarvis Studios, in development.", "games", body, wide=True)


def build_hot_crumb_placeholder(path, name, what):
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">Hot Crumb</p>
<h1>{name}</h1>
<ul class="doc-stamp"><li>Not yet published</li><li>No version in effect</li></ul>
</header>
<div class="note coral">
<p><strong>This document has not been written yet.</strong> Hot Crumb is in development and is not available to download. Its {what} will be published at this address before the game is released, with its version number and effective date.</p>
</div>
<p>Until then, see the <a href="{R}hot-crumb/">Hot Crumb page</a>, or email {email_link("Hot Crumb")} with any question.</p>
</article>"""
    page(path, f"{name} · Hot Crumb", f"Hot Crumb {name}: not yet published. Hot Crumb is in development.", "legal", body,
         crumbs=[("Home", ""), ("Legal", "legal/"), ("Hot Crumb", "hot-crumb/"), (name, None)])


def build_hot_crumb_support():
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">Hot Crumb</p>
<h1>Hot Crumb support</h1>
{stamp(SUPPORT_VERSION, PAGE_DATE, "Page version")}
</header>
<p>Hot Crumb is in development and is not available yet, so there is nothing to install, no account and no data to delete.</p>
<p>Questions are welcome: {email_link("Hot Crumb")}.</p>
<p><a href="{R}hot-crumb/">About Hot Crumb</a></p>
</article>"""
    page("hot-crumb/support/", "Support · Hot Crumb", "Support for Hot Crumb, a game in development by Jarvis Studios.", "support", body,
         crumbs=[("Home", ""), ("Support", "support/"), ("Hot Crumb", None)])


def build_news_index():
    body = f"""<h1>News</h1>
<p class="lead">What we are making, and what is new on this site.</p>
<div class="section">
{news_cards(NEWS, heading_level=2)}
</div>"""
    page("news/", "News", f"News from {STUDIO}: Turnstone, Hot Crumb and the studio.", "news", body, crumbs=[("Home", ""), ("News", None)])


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
<p class="lead">{STUDIO} is a small, independent studio that makes cozy games for phones. Warm, readable, and played with one thumb.</p>
</div>
{cat("look", "cat-about", "The studio cat, a ginger cat sitting up and looking at you")}
</div>
<section class="section prose" aria-labelledby="what">
<h2 id="what">What we believe</h2>
<p>A good phone game should fit around your day, not the other way round. So our games are turn-based and calm: nothing runs while you think, and every choice is yours to read before you make it.</p>
<ul>
<li><strong>Kind to your time.</strong> No lives, no energy and no timers that make you wait or hurry.</li>
<li><strong>Fair.</strong> Nothing you can buy wins for you. Ranked and daily challenges are the same for everyone.</li>
<li><strong>Readable.</strong> Color is never the only clue, and text sizes can grow.</li>
<li><strong>Private.</strong> We collect as little as we can, and we say exactly what in plain words.</li>
</ul>
</section>
<section class="section" aria-labelledby="our-games">
<h2 id="our-games">Our games</h2>
{game_cards()}
</section>
<section class="section prose" aria-labelledby="cat-h">
<h2 id="cat-h">And the cat?</h2>
<p>A ginger cat naps on the quay in Turnstone’s harbor. She has become the studio’s mascot, and she turns up wherever there is a warm spot to sleep. Look for her around this site.</p>
<p>Press and creators: see the <a href="{R}press/">press kit</a>. Everyone else: say hello at {email_link("Hello")}.</p>
</section>"""
    page("about/", "About", f"About {STUDIO}, a small studio making cozy, fair, one-thumb games for phones.", "about", body,
         crumbs=[("Home", ""), ("About", None)])


def build_accessibility():
    body = f"""<article class="prose">
<header class="doc-header">
<h1>Accessibility statement</h1>
<ul class="doc-stamp"><li>Page version 1</li><li>Updated <time datetime="{PAGE_DATE}">{nice_date(PAGE_DATE)}</time></li></ul>
</header>
<p class="lead">We want everyone to be able to use this website and play our games. This page says what we do, what we know is not right yet, and how to tell us about a problem.</p>
<h2 id="website">This website</h2>
<p>We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.2 at level AA. We check it ourselves; it has not been audited by an outside expert.</p>
<ul>
<li>Every page works with a keyboard alone, starts with a “Skip to content” link, and shows a clear outline on the part that has focus.</li>
<li>Text and buttons meet the AA contrast ratios, in both light and dark mode. The site follows your device’s light or dark setting.</li>
<li>Every image has a text description, or is marked as decoration when it adds nothing.</li>
<li>The pages work from 320 pixels wide, and text can be zoomed to 200% without losing content.</li>
<li>If your device asks for reduced motion, the site turns off its small animations. The gameplay video never plays by itself, has no sound, and comes with a written description.</li>
<li>The menus are real buttons with their state announced to screen readers.</li>
</ul>
<h2 id="games">Our games</h2>
<p>Turnstone is turn-based and played with taps only, in portrait, with one thumb. There are no timers. Every tile carries a symbol as well as a color, so color is never the only clue, and the game has a Text size setting (Default, Large and Larger).</p>
<p>Things we know are not right yet in Turnstone: there is no high-contrast option, and some screens still label only the selected tab of the main menu. We are working on both.</p>
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
        ("Studio key art: Otto and Mabel", "assets/press/jarvis-studios-key-art.jpg", "JPEG, 2400 × 1200"),
        ("Turnstone key art", "assets/press/turnstone-key-art.jpg", "JPEG, 2400 × 1200"),
        ("Otto the octopus", "assets/press/otto.png", "PNG, transparent"),
        ("Mabel the badger (early art)", "assets/press/mabel.png", "PNG, transparent"),
        ("Hot Crumb kitchen (early art)", "assets/press/hot-crumb-kitchen.jpg", "JPEG, 1024 × 1536"),
    ] + [(f"Turnstone screenshot: {cap}", f"assets/press/turnstone-{n}.jpg", "JPEG, 1170 × 2532") for n, cap, _ in SHOTS]
    dl = "\n".join(f'<li><a href="{R}{p}" download><span class="doc-name">{esc(t)}</span><span class="doc-meta">{esc(m)}</span></a></li>' for t, p, m in downloads)
    body = f"""<h1>Press kit</h1>
<p class="lead">Facts, art and screenshots for writing about {STUDIO} and our games.</p>
<div class="press-hero">{pic("home/hero-wide", [1200, 1800], "(min-width: 1100px) 1048px, 92vw", "Otto the octopus and Mabel the badger baker on a sunny stone quay, with the studio cat between them", 2400, 1200, cls="panel-img")}</div>
<section class="section" aria-labelledby="facts">
<h2 id="facts">Fact sheet</h2>
<dl class="fact-sheet">
<div><dt>Studio</dt><dd>{STUDIO}, an independent game studio</dd></div>
<div><dt>Games</dt><dd><a href="{R}turnstone/">Turnstone</a> (tile puzzle) and <a href="{R}hot-crumb/">Hot Crumb</a> (bakery card game)</dd></div>
<div><dt>Platforms</dt><dd>iOS and Android (Turnstone coming soon; Hot Crumb in development)</dd></div>
<div><dt>Price</dt><dd>Not announced</dd></div>
<div><dt>Characters</dt><dd>Otto, a round purple octopus (Turnstone); Mabel, a badger baker (Hot Crumb); and the studio cat</dd></div>
<div><dt>In one line</dt><dd>Cozy, fair games for one thumb: turn-based, no lives, no energy, nothing that wins for you.</dd></div>
<div><dt>Press contact</dt><dd>{email_link("Press")}</dd></div>
</dl>
</section>
<section class="section" aria-labelledby="dl">
<h2 id="dl">Downloads</h2>
<ul class="doc-list">
{dl}
</ul>
<p class="muted small">You may use these images to write about our games. Please don’t change the characters or the wordmark. Hot Crumb art is early work in progress. Screenshots are from a test build.</p>
</section>"""
    page("press/", "Press kit", f"The {STUDIO} press kit: fact sheet, wordmark, key art and screenshots.", "about", body,
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
<p class="lead">The studio cat looked all around the harbor, but there is no page at this address. She has gone back to sleep.</p>
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
    build_legal_doc("turnstone/terms/", "Terms of Use", "terms_of_use", TS_TERMS_META, TS_TERMS, ("turnstone/privacy/", "Privacy Policy"))
    build_legal_doc("turnstone/privacy/", "Privacy Policy", "privacy_policy", TS_PRIV_META, TS_PRIV, ("turnstone/terms/", "Terms of Use"))
    build_delete_data()
    build_turnstone_support()
    build_support()
    build_legal_index()
    build_hot_crumb()
    build_hot_crumb_placeholder("hot-crumb/terms/", "Terms of Use", "Terms of Use")
    build_hot_crumb_placeholder("hot-crumb/privacy/", "Privacy Policy", "Privacy Policy")
    build_hot_crumb_support()
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
