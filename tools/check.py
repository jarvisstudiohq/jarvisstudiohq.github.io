#!/usr/bin/env python3
"""Checks the Jarvis Studios website before it is published. Standard library only.

    python3 tools/check.py                                 # links, paths, legal text vs content/, email, images
    python3 tools/check.py --game-legal <dir>              # also: content/turnstone/*.txt equal the game's legal/*.txt
    python3 tools/check.py --release                       # also: the support email placeholder must be replaced

<dir> is the game's `godot-production/legal` folder (or set TURNSTONE_LEGAL_DIR). Exit code 0 = every check passed.

What it verifies:
1. Every internal link, image, stylesheet and script resolves to a file in the site, including #fragments.
2. No root-absolute paths ("/x" or "//host"): the site must work at a domain root and under a subpath.
3. No absolute address of the site itself in any page (the only place for one is siteUrl in assets/js/config.js).
4. No external scripts, and no external stylesheets except Google Fonts. No cookies, storage or analytics code.
5. Each Turnstone legal page shows the game's text word for word, with the version and effective date from its @meta line.
6. Every page has lang, a <title>, a description and one <h1>. Document pages show a version (or "Not yet published") and a date.
7. Every shown support email equals supportEmail in config.js (the pages were rebuilt after it changed).
8. Every image in assets/img is at most 250 KB, and every <img> has an alt attribute.
"""

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
MAX_IMAGE = 250 * 1024
ALLOWED_CSS_HOSTS = {"fonts.googleapis.com"}
ALLOWED_PRECONNECT = {"fonts.googleapis.com", "fonts.gstatic.com"}
PLACEHOLDER = "REPLACE-ME"
DOC_PAGES = ["turnstone/terms/", "turnstone/privacy/", "turnstone/delete-data/", "turnstone/support/",
             "hot-crumb/terms/", "hot-crumb/privacy/", "hot-crumb/support/"]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


class Page(HTMLParser):
    """Collects the references, ids, headings, titles, email elements and the text of legal blocks."""

    BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "td", "th", "dt", "dd", "summary", "figcaption"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []            # (tag, attr, value)
        self.ids = set()
        self.h1 = 0
        self.title = ""
        self.lang = ""
        self.description = None
        self.in_title = False
        self.email_nodes = []     # text of [data-support-email] elements
        self._email_depth = 0
        self._email_buf = []
        self.legal = []           # dicts: source, version, date, blocks
        self._legal_depth = 0
        self._stack = []
        self._block_buf = None
        self.imgs_without_alt = 0
        self.text_all = []
        self.has_time = False
        self.stamps = []
        self._in_stamp = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stack.append(tag)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1 += 1
        if tag == "time":
            self.has_time = True
        if tag == "meta" and a.get("name") == "description":
            self.description = a.get("content", "")
        if tag == "img" and "alt" not in a:
            self.imgs_without_alt += 1
        if tag == "ul" and "doc-stamp" in (a.get("class") or "").split():
            self._in_stamp = len(self._stack)
        for attr in ("href", "src"):
            if attr in a and a[attr] is not None:
                self.refs.append((tag, attr, a[attr], a.get("rel", "")))
        if "srcset" in a and a["srcset"]:
            for part in a["srcset"].split(","):
                u = part.strip().split(" ")[0]
                if u:
                    self.refs.append((tag, "srcset", u, ""))
        if "data-support-email" in a:
            self._email_depth = len(self._stack)
            self._email_buf = []
        if "data-legal-source" in a:
            self._legal_depth = len(self._stack)
            self.legal.append({"source": a["data-legal-source"], "version": a.get("data-version"),
                               "date": a.get("data-effective-date"), "blocks": []})
        if self._legal_depth and tag in self.BLOCK:
            self._block_buf = []

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if self._legal_depth and tag in self.BLOCK and self._block_buf is not None:
            self.legal[-1]["blocks"].append("".join(self._block_buf))
            self._block_buf = None
        depth = len(self._stack)
        if self._email_depth and depth == self._email_depth:
            self.email_nodes.append("".join(self._email_buf).strip())
            self._email_depth = 0
        if self._legal_depth and depth == self._legal_depth:
            self._legal_depth = 0
        if self._in_stamp and depth == self._in_stamp:
            self._in_stamp = 0
        if self._stack:
            self._stack.pop()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self._email_depth:
            self._email_buf.append(data)
        if self._block_buf is not None:
            self._block_buf.append(data)
        if self._in_stamp:
            self.stamps.append(data)
        self.text_all.append(data)


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class PageVoidAware(Page):
    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        if tag in VOID and self._stack and self._stack[-1] == tag:
            self._stack.pop()


def parse(path):
    p = PageVoidAware()
    p.feed(path.read_text(encoding="utf-8"))
    p.close()
    return p


def html_files():
    return sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "tools" not in p.parts)


def page_dir(path):
    """The folder URL a page is served from, relative to the site root ("" for the root)."""
    rel = path.relative_to(ROOT)
    return "" if len(rel.parts) == 1 else "/".join(rel.parts[:-1]) + "/"


def resolve(base_dir, ref):
    """Resolve a relative reference against a site folder; returns (site path, fragment) or None if it leaves the site."""
    parts = urlsplit(ref)
    path = unquote(parts.path)
    segs = (base_dir + path).split("/") if path else (base_dir + "index.html").split("/")
    out = []
    for s in segs[:-1]:
        if s in ("", "."):
            continue
        if s == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(s)
    last = segs[-1]
    if last == "..":
        if not out:
            return None
        out.pop()
        last = ""
    elif last == ".":
        last = ""
    target = "/".join(out + ([last] if last else []))
    if path.endswith("/") or last == "" or path == "":
        target = (target + "/" if target else "") + "index.html"
    if not path:  # a pure "#fragment" or "?query" link: the page itself
        target = None
    return target, parts.fragment


def check_links(pages):
    ids_by_file = {str(p.relative_to(ROOT)): parsed.ids for p, parsed in pages.items()}
    for path, parsed in pages.items():
        name = str(path.relative_to(ROOT))
        base = page_dir(path)
        for tag, attr, ref, rel in parsed.refs:
            r = ref.strip()
            if tag == "base":
                if r not in ("./", ""):
                    err(f"{name}: <base href=\"{r}\"> must be relative (\"./\")")
                continue
            if r.startswith("//") or (r.startswith("/") and not r.startswith("//")):
                err(f"{name}: root-absolute path {r!r} ({tag} {attr}); use a relative path")
                continue
            scheme = urlsplit(r).scheme
            if scheme in ("mailto", "data", "tel"):
                continue
            if scheme in ("http", "https"):
                host = urlsplit(r).netloc
                if tag == "script":
                    err(f"{name}: external script {r}")
                elif tag == "link" and "stylesheet" in rel and host not in ALLOWED_CSS_HOSTS:
                    err(f"{name}: external stylesheet {r}")
                elif tag == "link" and "preconnect" in rel and host not in ALLOWED_PRECONNECT:
                    err(f"{name}: unexpected preconnect {r}")
                elif tag in ("img", "source", "iframe", "video", "audio"):
                    err(f"{name}: external media {r}")
                continue
            if scheme:
                err(f"{name}: unsupported link scheme {r}")
                continue
            res = resolve(base, r)
            if res is None:
                err(f"{name}: {r!r} points outside the site")
                continue
            target, frag = res
            if target is None:
                target = name
            if not (ROOT / target).is_file():
                err(f"{name}: broken link {r!r} -> {target}")
                continue
            if frag and target.endswith(".html"):
                tids = ids_by_file.get(target)
                if tids is None:
                    tids = parse(ROOT / target).ids
                if frag not in tids and frag != "main":
                    err(f"{name}: {r!r} -> #{frag} not found in {target}")


def check_text_rules(pages):
    for path, parsed in pages.items():
        name = str(path.relative_to(ROOT))
        src = path.read_text(encoding="utf-8")
        if "github.io" in src:
            err(f"{name}: contains an absolute site address (github.io); keep links relative")
        if not parsed.lang:
            err(f"{name}: <html> has no lang")
        if not parsed.title.strip():
            err(f"{name}: no <title>")
        if parsed.description is None and name != "404.html":
            err(f"{name}: no meta description")
        if parsed.h1 != 1:
            err(f"{name}: has {parsed.h1} <h1> elements (want 1)")
        if parsed.imgs_without_alt:
            err(f"{name}: {parsed.imgs_without_alt} <img> without alt")
    for f in list(ROOT.rglob("*.js")) + list(ROOT.rglob("*.html")):
        if ".git" in f.parts or "tools" in f.parts:
            continue
        s = f.read_text(encoding="utf-8")
        for bad in ("document.cookie", "localStorage", "sessionStorage", "indexedDB", "gtag(", "google-analytics",
                    "googletagmanager", "plausible", "fbq(", "navigator.sendBeacon"):
            if bad in s:
                err(f"{f.relative_to(ROOT)}: contains {bad!r} (the site has no cookies, storage or analytics)")


def legal_source_blocks(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    meta = json.loads(lines[0][6:]) if lines and lines[0].startswith("@meta ") else None
    paras = [p.strip() for p in "\n".join(lines[1:]).split("\n\n") if p.strip()]
    out = []
    for p in paras:
        if p.startswith("# "):
            p = p[2:]
        elif p.startswith("• "):
            p = p[2:]
        out.append(p.strip())
    return meta, out


def norm(s):
    return " ".join(s.split())


def check_legal(pages, game_dir):
    found = 0
    for path, parsed in pages.items():
        name = str(path.relative_to(ROOT))
        for doc in parsed.legal:
            found += 1
            src = ROOT / doc["source"]
            if not src.is_file():
                err(f"{name}: legal source {doc['source']} missing")
                continue
            meta, want = legal_source_blocks(src)
            got = [norm(b) for b in doc["blocks"]]
            want = [norm(b) for b in want]
            if got != want:
                for i, (g, w) in enumerate(zip(got, want)):
                    if g != w:
                        err(f"{name}: legal text differs from {doc['source']} at block {i + 1}:\n    page: {g[:160]}\n    game: {w[:160]}")
                        break
                else:
                    err(f"{name}: legal text has {len(got)} blocks, {doc['source']} has {len(want)}")
            elif " ".join(got).split() != " ".join(want).split():
                err(f"{name}: legal text words differ from {doc['source']}")
            if meta is None:
                err(f"{doc['source']}: no @meta line")
                continue
            if str(meta.get("version")) != str(doc["version"]) or meta.get("effective_date") != doc["date"]:
                err(f"{name}: version/date attributes {doc['version']}/{doc['date']} differ from {doc['source']} @meta")
            stamp = " ".join(parsed.stamps)
            if f"Version {meta.get('version')}" not in stamp:
                err(f"{name}: does not show 'Version {meta.get('version')}'")
            y, m, d = meta["effective_date"].split("-")
            if y not in stamp or str(int(d)) not in stamp:
                err(f"{name}: does not show the effective date {meta['effective_date']}")
    if found < 2:
        err(f"expected at least 2 legal documents on the site, found {found}")
    if game_dir:
        g = Path(game_dir).expanduser()
        if not g.is_dir():
            err(f"--game-legal {game_dir}: not a folder")
        else:
            for f in sorted((ROOT / "content/turnstone").glob("*.txt")):
                other = g / f.name
                if not other.is_file():
                    err(f"{f.name}: not in the game's legal folder")
                elif other.read_bytes() != f.read_bytes():
                    err(f"content/turnstone/{f.name} differs from the game's {f.name}: copy it over and run tools/build.py")
            extra = {p.name for p in g.glob("*.txt")} - {p.name for p in (ROOT / "content/turnstone").glob("*.txt")}
            if extra:
                err(f"the game has legal documents the site does not publish: {sorted(extra)}")
    return found


def check_doc_pages(pages):
    by_name = {str(p.relative_to(ROOT)): parsed for p, parsed in pages.items()}
    for d in DOC_PAGES:
        parsed = by_name.get(d + "index.html")
        if parsed is None:
            err(f"stable URL {d} has no page")
            continue
        stamp = " ".join(parsed.stamps)
        if not stamp:
            err(f"{d}: shows no version/date stamp")
        elif "Not yet published" not in stamp and not ("ersion" in stamp and parsed.has_time):
            err(f"{d}: stamp must show a version and an effective date: {stamp!r}")


def check_email(pages, release):
    cfg = (ROOT / "assets/js/config.js").read_text(encoding="utf-8")
    m = re.search(r'supportEmail\s*:\s*"([^"]*)"', cfg)
    if not m:
        err("assets/js/config.js: supportEmail not found")
        return None
    email = m.group(1).strip()
    n = 0
    for path, parsed in pages.items():
        for t in parsed.email_nodes:
            n += 1
            if t != email:
                err(f"{path.relative_to(ROOT)}: shows {t!r} but config.js says {email!r}; run tools/build.py")
    if n == 0:
        err("no page shows the support email")
    if PLACEHOLDER in email:
        (err if release else warn)(f"support email is still the placeholder {email!r} (assets/js/config.js)")
    # nothing else may hard-code an address
    for f in list(ROOT.rglob("*.html")) + list(ROOT.rglob("*.js")):
        if ".git" in f.parts or "tools" in f.parts:
            continue
        for addr in set(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", f.read_text(encoding="utf-8"))):
            if addr != email and PLACEHOLDER not in addr:
                err(f"{f.relative_to(ROOT)}: hard-coded email {addr}")
    return email, n


def check_images():
    for f in sorted((ROOT / "assets/img").rglob("*")):
        if f.is_file() and f.stat().st_size > MAX_IMAGE:
            err(f"{f.relative_to(ROOT)} is {f.stat().st_size // 1024} KB (max 250 KB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--game-legal", default=os.environ.get("TURNSTONE_LEGAL_DIR", ""),
                    help="the game's godot-production/legal folder, to compare the legal texts with")
    ap.add_argument("--release", action="store_true", help="fail while the support email is still the placeholder")
    args = ap.parse_args()

    files = html_files()
    pages = {p: parse(p) for p in files}
    check_links(pages)
    check_text_rules(pages)
    n_legal = check_legal(pages, args.game_legal)
    check_doc_pages(pages)
    em = check_email(pages, args.release)
    check_images()

    n_refs = sum(len(p.refs) for p in pages.values())
    print(f"check: {len(files)} pages, {n_refs} references, {n_legal} legal documents"
          + (f", {em[1]} support-email spots ({em[0]})" if em else ""))
    print("check: legal text compared with content/turnstone/*.txt"
          + (f" and with {args.game_legal}" if args.game_legal else " (pass --game-legal to compare with the game too)"))
    for w in warnings:
        print("WARNING: " + w)
    for e in errors:
        print("ERROR: " + e)
    print("check: " + ("FAILED" if errors else "OK"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
