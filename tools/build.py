#!/usr/bin/env python3
"""Builds every HTML page of the Jarvis Studios website from one layout.

    python3 tools/build.py

The output is plain HTML committed next to this script's folder, so GitHub Pages serves the site as it is (no build runs there).
Run this after changing a page below, the support email in assets/js/config.js, or a legal text in content/.

Rules the output follows (tools/check.py verifies them):
- Every link and asset path is relative (no leading "/"), so the site works both at a domain root
  (https://jarvisstudio.github.io/) and under a subpath (https://cjarvis0.github.io/jarvis-studio/).
- Turnstone's legal pages are generated from content/turnstone/*.txt, verbatim copies of the game's own legal files.
- The support email has one source: supportEmail in assets/js/config.js.
"""

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO = "Jarvis Studios"
FONTS = ("https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600"
         "&family=Grandstander:wght@700;800;900&family=Ultra&display=swap")

NAV = [("home", "Home", ""), ("games", "Games", "games/"), ("support", "Support", "support/"), ("legal", "Legal", "legal/")]


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


# ---------------------------------------------------------------- layout

def picture(rel, name, alt, w, h, eager=False):
    base = f"{rel}assets/img/turnstone/{name}"
    load = "" if eager else ' loading="lazy"'
    return (f'<picture><source type="image/webp" srcset="{base}.webp">'
            f'<img src="{base}.jpg" width="{w}" height="{h}" alt="{esc(alt)}"{load} decoding="async"></picture>')


def harbor(rel, cls="scene", eager=False):
    b = f"{rel}assets/img/turnstone/harbor"
    load = "" if eager else ' loading="lazy"'
    return (f'<picture><source type="image/webp" srcset="{b}-768.webp 768w, {b}-1536.webp 1536w" sizes="(min-width: 1080px) 1080px, 100vw">'
            f'<img class="{cls}" src="{b}-768.jpg" srcset="{b}-768.jpg 768w, {b}-1536.jpg 1536w" sizes="(min-width: 1080px) 1080px, 100vw" '
            f'width="1536" height="694" alt=""{load} decoding="async"></picture>')


def page(path, title, description, nav, body, crumbs=None):
    """path: the output folder relative to the site root ("" for the home page, "turnstone/privacy/" ...)."""
    depth = path.count("/")
    rel = "../" * depth
    full_title = title if title == STUDIO else f"{title} · {STUDIO}"
    nav_items = []
    for key, label, href in NAV:
        cur = ' aria-current="page"' if key == nav else ""
        nav_items.append(f'<li><a href="{rel}{href}"{cur}>{label}</a></li>' if href else
                         f'<li><a href="{rel or "./"}"{cur}>{label}</a></li>')
    crumb_html = ""
    if crumbs:
        items = []
        for label, href in crumbs:
            if href is None:
                items.append(f'<li aria-current="page">{esc(label)}</li>')
            else:
                items.append(f'<li><a href="{rel}{href}">{esc(label)}</a></li>' if href else
                             f'<li><a href="{rel or "./"}">{esc(label)}</a></li>')
        crumb_html = f'<nav class="breadcrumb" aria-label="Breadcrumb"><ol>{"".join(items)}</ol></nav>\n'
    home = rel or "./"
    doc = f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#fff8e6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f252b" media="(prefers-color-scheme: dark)">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{rel}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{rel}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{rel}assets/css/site.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
<div class="wrap">
<a class="wordmark" href="{home}" aria-label="{STUDIO}, home"><span class="wm-top" aria-hidden="true">JARVIS</span><span class="wm-bottom" aria-hidden="true">STUDIOS</span></a>
<nav class="site-nav" aria-label="Main">
<ul>
{chr(10).join(nav_items)}
</ul>
</nav>
</div>
</header>
<main id="main" tabindex="-1">
<div class="wrap">
{crumb_html}{body.replace("{rel}", rel).replace("{home}", home)}
</div>
</main>
<footer class="site-footer">
<div class="wrap">
<ul>
<li><a href="{rel}games/">Games</a></li>
<li><a href="{rel}support/">Support</a></li>
<li><a href="{rel}legal/">Legal</a></li>
<li><a href="{rel}legal/#this-website">About this website</a></li>
</ul>
<p>Support: {email_link()}</p>
<p>© 2026 {STUDIO}. This website uses no cookies, no analytics and no trackers.</p>
</div>
</footer>
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


def turnstone_docs_list(rel_prefix="{rel}"):
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


def hotcrumb_docs_list(rel_prefix="{rel}"):
    rows = [
        ("hot-crumb/terms/", "Terms of Use", "Not yet published"),
        ("hot-crumb/privacy/", "Privacy Policy", "Not yet published"),
        ("hot-crumb/support/", "Support", "Contact"),
    ]
    return '<ul class="doc-list">\n' + "\n".join(
        f'<li><a href="{rel_prefix}{h}"><span class="doc-name">{n}</span><span class="doc-meta">{m}</span></a></li>'
        for h, n, m in rows) + "\n</ul>"


def game_cards():
    return f"""<div class="card-grid">
<article class="card">
<div class="card-art">{harbor("{rel}")}<img class="mascot" src="{{rel}}assets/img/turnstone/otto-happy.svg" width="320" height="280" alt="Otto, a round purple octopus, smiling"></div>
<div class="card-body">
<span class="badge">Coming to iOS and Android</span>
<h3><a href="{{rel}}turnstone/">Turnstone</a></h3>
<p>A cozy, turn-based tile puzzle in a sunny harbor, played with one thumb. No timers, no lives, no energy.</p>
<p class="card-links"><a href="{{rel}}turnstone/privacy/">Privacy</a><a href="{{rel}}turnstone/terms/">Terms</a><a href="{{rel}}turnstone/support/">Support</a></p>
</div>
</article>
<article class="card">
<div class="card-art soon" aria-hidden="true"><span>Hot Crumb</span></div>
<div class="card-body">
<span class="badge coral">In development</span>
<h3><a href="{{rel}}hot-crumb/">Hot Crumb</a></h3>
<p>A cozy bakery card game for one thumb, starring Mabel the badger baker. Pick ingredients, bake recipes everyone knows, and see the score before you commit.</p>
</div>
</article>
</div>"""


# ---------------------------------------------------------------- pages

def build_home():
    body = f"""<section class="studio-card" aria-labelledby="studio-name">
<h1 class="big-wordmark" id="studio-name"><span class="wm-top">JARVIS</span><span class="wm-bottom">STUDIOS</span></h1>
<p class="tagline">Cozy, hand-made games for phones.</p>
</section>
<div class="intro">
<p>{STUDIO} is a small studio that makes warm, readable games you can play with one thumb: no timers that rush you, no lives or energy that make you wait, and nothing you can buy that wins for you.</p>
</div>
<section class="section" aria-labelledby="our-games">
<h2 id="our-games">Our games</h2>
{game_cards()}
</section>
<section class="section" aria-labelledby="help">
<h2 id="help">Help and documents</h2>
<p>Questions, or want to delete your game data? See <a href="{{rel}}support/">Support</a>. Every game’s Terms of Use and Privacy Policy are on the <a href="{{rel}}legal/">Legal</a> page.</p>
</section>"""
    page("", STUDIO, f"{STUDIO} makes cozy, hand-made games for phones. Home of Turnstone and Hot Crumb.", "home", body)


def build_games():
    body = f"""<h1>Games</h1>
<p class="lead">Two games so far, both made for one thumb and a few quiet minutes.</p>
<div class="section">
{game_cards()}
</div>"""
    page("games/", "Games", f"Games by {STUDIO}: Turnstone and Hot Crumb.", "games", body, crumbs=[("Home", ""), ("Games", None)])


def build_turnstone():
    shots = [
        ("home", "Home", "The Home screen: Otto floats in the harbor in front of the town, with a big PLAY button for the next level and buttons for Community, Open Tide, the Daily Tile and a Tide Jar."),
        ("gameplay", "A level", "A level in progress: a board of glazed tiles marked with stars, leaves, shells and sails, the goals and the moves left at the top, and Otto watching from the quay."),
        ("level-cleared", "Level cleared", "The Level Cleared card: two gold stars, a basket of shells and +23 Shells earned, with a Continue button."),
        ("harbor-jar", "A Harbor Jar", "Opening a Harbor Jar at sunset: Otto grins beside the jar and a big shell shows +70 Shells."),
        ("profile", "Profile", "The Profile page: Otto's portrait on a pedestal with the harbor rank, progress toward the next rank and a showcase for badges."),
    ]
    shot_html = "\n".join(
        f'<li><figure>{picture("{rel}", n, alt, 540, 1168)}<figcaption>{cap}</figcaption></figure></li>' for n, cap, alt in shots)
    body = f"""<section class="game-hero">
{harbor("{rel}", eager=True)}
<img class="mascot" src="{{rel}}assets/img/turnstone/otto-celebrate.svg" width="320" height="280" alt="Otto the octopus, cheering with two arms raised">
<div class="title-plate"><h1>Turnstone</h1><p>by {STUDIO}</p></div>
</section>
<div class="section">
<span class="badge">Coming to iOS and Android</span>
<p class="lead" style="margin-top:12px">{TS_PITCH}</p>
<p style="max-width:60ch">Play the campaign through the harbor, try the Daily puzzle that is the same for everyone and is played without Tools, and build your own levels in the level maker.</p>
</div>
<section class="section" aria-labelledby="facts">
<h2 id="facts">Good to know</h2>
<ul class="facts">
<li><strong>One thumb, taps only</strong>Portrait, turn-based, no timers.</li>
<li><strong>No lives, no energy</strong>You never have to wait, or pay, to keep playing.</li>
<li><strong>Plays offline</strong>This version keeps your progress on your device and needs no account.</li>
<li><strong>No ads, nothing for sale</strong>This version shows no ads and sells nothing for real money.</li>
<li><strong>Fair Daily</strong>Nothing you can buy is ever usable in the ranked Daily puzzle, and stars are never sold.</li>
<li><strong>For all ages</strong>Players under 13 pick their name from a list instead of typing one.</li>
</ul>
</section>
<section class="section" aria-labelledby="shots">
<h2 id="shots">Screenshots</h2>
<ul class="shots">
{shot_html}
</ul>
<p class="muted">Screenshots from a test build. Names and numbers are examples made up by the game.</p>
</section>
<section class="section" aria-labelledby="docs">
<h2 id="docs">Documents and support</h2>
{turnstone_docs_list()}
</section>"""
    page("turnstone/", "Turnstone", "Turnstone is a cozy, one-thumb, turn-based tile puzzle starring Otto the octopus. Coming to iOS and Android.",
         "games", body, crumbs=[("Home", ""), ("Games", "games/"), ("Turnstone", None)])


def contact_note(doc_name):
    return f"""<aside class="note" aria-labelledby="contact-note">
<h2 id="contact-note">Contact by email</h2>
<p>The {doc_name} above says that the game does not yet include a way to send us a message. You can also email us at {email_link("Turnstone " + doc_name)}. This note is part of this website, not of the {doc_name}.</p>
</aside>"""


def build_legal_doc(path, name, short, meta, blocks, other):
    v, d = meta["version"], meta["effective_date"]
    oth_path, oth_name = other
    body = f"""<article class="prose">
<header class="doc-header">
<p class="eyebrow">Turnstone</p>
<h1>{name}</h1>
{stamp(v, d)}
</header>
<p class="muted">This is the exact text of version {v}, the version the game shows in Settings, under About. See also the <a href="{{rel}}{oth_path}">{oth_name}</a>.</p>
<div class="legal-doc" data-legal-source="content/turnstone/{short}.txt" data-version="{v}" data-effective-date="{d}">
{legal_html(blocks)}
</div>
</article>
{contact_note(name)}"""
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
<p>This version of Turnstone keeps all of its data on your device and sends none of it to us (see section 6 of the <a href="{{rel}}turnstone/privacy/">Privacy Policy</a>, version {pv}, effective {nice_date(pd)}). That is why deleting happens on the device.</p>

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
<p>Email {email_link("Turnstone data deletion")}. When a later version adds an online account, this page and the Privacy Policy will be updated to explain how deleting the account works.</p>
</article>"""
    page("turnstone/delete-data/", "Delete your data · Turnstone",
         "How to delete everything Turnstone keeps about you, using Delete my data in the game's Settings.", "legal", body,
         crumbs=[("Home", ""), ("Legal", "legal/"), ("Turnstone", "turnstone/"), ("Delete your data", None)])


def turnstone_faq():
    return f"""<div class="faq">
<details open>
<summary>How do I delete my data?</summary>
<div><p>In the game: <span class="ui-label">Settings</span> › <span class="ui-label">Account and social</span> › <span class="ui-label">Delete my data</span>, then confirm with <span class="ui-label">Yes, delete everything</span>. Turnstone erases everything it keeps on your device and starts fresh the next time you open it. The full steps are on <a href="{{rel}}turnstone/delete-data/">Delete your data</a>.</p></div>
</details>
<details>
<summary>How do I contact you?</summary>
<div><p>Email {email_link("Turnstone support")}. This version of the game does not yet include a way to send us a message from inside the game.</p></div>
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
<div><p>Once, the first time you open it, so it can set itself up for you. For example, players under 13 pick their name from a list instead of typing one. It keeps only an age group, never your birthday or exact age. See section 5 of the <a href="{{rel}}turnstone/privacy/">Privacy Policy</a>.</p></div>
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
<p><a href="{{rel}}turnstone/support/">All Turnstone support</a> · <a href="{{rel}}turnstone/delete-data/">Delete your Turnstone data</a></p>
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
<h2 id="ts-docs"><a href="{{rel}}turnstone/">Turnstone</a></h2>
{turnstone_docs_list()}
</section>
<section class="section" aria-labelledby="hc-docs">
<h2 id="hc-docs"><a href="{{rel}}hot-crumb/">Hot Crumb</a></h2>
<p class="muted">Hot Crumb is in development. Its documents will be published here before the game is released.</p>
{hotcrumb_docs_list()}
</section>
<section class="section prose" aria-labelledby="this-website">
<h2 id="this-website">This website</h2>
<p>This website uses no cookies, no analytics, no advertising and no trackers, and it has no forms. It stores nothing in your browser.</p>
<p>Its fonts (Grandstander, Fredoka and Ultra) are loaded from Google Fonts, so your browser asks Google’s servers for them, as it does on any site that uses Google Fonts. The site is hosted on GitHub Pages, and GitHub may keep basic logs of visits, such as IP addresses, under its own privacy statement. We do not receive or use those logs.</p>
<p>If you email us, we use your message and email address only to answer you.</p>
</section>"""
    page("legal/", "Legal", f"Terms of Use, Privacy Policies and data deletion for every {STUDIO} game.", "legal", body,
         crumbs=[("Home", ""), ("Legal", None)])


def build_hot_crumb():
    body = f"""<article>
<header class="doc-header prose">
<span class="badge coral">In development</span>
<h1 style="margin-top:10px">Hot Crumb</h1>
<p class="muted">by {STUDIO}. Not yet available.</p>
</header>
<p class="lead">{HC_PITCH}</p>
<p>Hold your Flour back and it rises, so tomorrow’s bake is bigger, if you can afford to wait. Please the picky village Regulars, spend coins at the Market on better ingredients and charming Kitchen Helpers that bend the rules, and get through a week of rising targets to win the Royal Tasting. A run takes 15 to 20 minutes, and you can pause after any bake.</p>
<ul class="facts section">
<li><strong>One thumb, taps only</strong>Portrait and turn-based. No timer runs while you think.</li>
<li><strong>Readable before you bake</strong>Flavor × Warmth = Delight, shown in full before you tap Bake.</li>
<li><strong>Fair, always</strong>No energy, no lives, and nothing paid touches a run.</li>
</ul>
<h2 class="section">Documents</h2>
<p class="muted">Hot Crumb has no Terms of Use or Privacy Policy yet. They will be published here before the game is released.</p>
{hotcrumb_docs_list()}
</article>"""
    page("hot-crumb/", "Hot Crumb", "Hot Crumb is a cozy bakery card game for one thumb by Jarvis Studios, in development.", "games", body,
         crumbs=[("Home", ""), ("Games", "games/"), ("Hot Crumb", None)])


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
<p>Until then, see the <a href="{{rel}}hot-crumb/">Hot Crumb page</a>, or email {email_link("Hot Crumb")} with any question.</p>
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
<p><a href="{{rel}}hot-crumb/">About Hot Crumb</a></p>
</article>"""
    page("hot-crumb/support/", "Support · Hot Crumb", "Support for Hot Crumb, a game in development by Jarvis Studios.", "support", body,
         crumbs=[("Home", ""), ("Support", "support/"), ("Hot Crumb", None)])


def build_404():
    """GitHub Pages serves 404.html for a missing address at ANY depth, so relative paths cannot be trusted there. The page carries its
    own styles and art inline, and a small script finds the site root (siteUrl from config.js if set; otherwise it looks for
    site-root.txt in each parent folder of the address) and points <base> at it, which fixes every link on the page."""
    css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    otto = (ROOT / "assets/img/turnstone/otto-happy.svg").read_text(encoding="utf-8")
    otto = otto.replace("<svg ", '<svg role="img" aria-label="Otto the octopus" ', 1)
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
    nav = "\n".join(f'<li><a href="{href or "./"}">{label}</a></li>' for _, label, href in NAV)
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
.not-found svg {{ width: 200px; height: auto; margin: 0 auto 10px; display: block; }}
</style>
<script>
{script}
</script>
</head>
<body>
<a class="skip-link" href="#main" onclick="document.getElementById('main').focus(); return false;">Skip to content</a>
<header class="site-header">
<div class="wrap">
<a class="wordmark" href="./" aria-label="{STUDIO}, home"><span class="wm-top" aria-hidden="true">JARVIS</span><span class="wm-bottom" aria-hidden="true">STUDIOS</span></a>
<nav class="site-nav" aria-label="Main">
<ul>
{nav}
</ul>
</nav>
</div>
</header>
<main id="main" tabindex="-1">
<div class="wrap not-found">
{otto}
<h1>Page not found</h1>
<p class="lead">Otto looked all around the harbor, but there is no page at this address.</p>
<p><a class="button" href="./">Go to the home page</a></p>
<p>Looking for a game’s documents? Try <a href="legal/">Legal</a> or <a href="support/">Support</a>.</p>
</div>
</main>
<footer class="site-footer">
<div class="wrap">
<p>© 2026 {STUDIO}. This website uses no cookies, no analytics and no trackers.</p>
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
    build_404()
    pages = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    print(f"build: wrote {len(pages)} pages (support email: {EMAIL})")
    for p in pages:
        print("  " + p)


if __name__ == "__main__":
    main()
