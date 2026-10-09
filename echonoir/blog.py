"""Built-in static blog: one HTML page per published story, an index, blog.xml and style.css.

Everything is generated into the same site/ folder as the podcast feed, so one upload
command and one web server serve both. The whole blog is rebuilt from the episodes
folder on every publish, which keeps prev/next links and the index consistent.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import html
import re
from pathlib import Path
from typing import List, Optional

from . import episodes
from .config import Config
from .styles import STYLES

SCENE_BREAK_RE = re.compile(r"^\s*\*\s*\*\s*\*\s*$", flags=re.M)

CSS = """\
:root{--bg:#101212;--panel:#181b1b;--text:#e6e0cc;--head:#fff9e1;--soft:#cfc9b6;--muted:#9aa59f;--accent:#45c4bd;--glow:#e8b872;--line:#2b3634}
*{box-sizing:border-box}
html{color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--text);font:18px/1.75 Georgia,"Iowan Old Style","Times New Roman",serif;
-webkit-text-size-adjust:100%}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:40rem;margin:0 auto;padding:0 1.25rem}
header.site{border-bottom:1px solid var(--line);padding:1.1rem 0;margin-bottom:2.2rem}
header.site .wrap{display:flex;justify-content:space-between;align-items:baseline;gap:1rem;flex-wrap:wrap}
header.site .brand{font-size:1.15rem;letter-spacing:.18em;text-transform:uppercase;color:var(--text)}
header.site nav a{margin-left:1.2rem;font:0.8rem/1 -apple-system,"Helvetica Neue",Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase}
h1,h2{color:var(--head)}
h1{font-size:2.1rem;line-height:1.2;margin:.2rem 0 .6rem;font-weight:normal}
.card h2 a{color:var(--head)}.card h2 a:hover{color:var(--accent);text-decoration:none}
.herobox{display:flex;gap:1.4rem;align-items:flex-start}.herobox img{width:7.5rem;height:7.5rem;object-fit:cover;border-radius:8px;border:1px solid var(--line);flex:none}
.meta,.tags,.small{font:0.8rem/1.5 -apple-system,"Helvetica Neue",Arial,sans-serif;color:var(--muted);letter-spacing:.04em}
.lede{font-style:italic;color:var(--soft);margin:1rem 0 1.4rem}
.tags span{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:.05rem .65rem;margin:0 .35rem .35rem 0}
.player{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:.9rem 1rem;margin:1.4rem 0 2rem}
.player audio{width:100%;margin-top:.5rem}
article p{margin:0 0 1.15em}
article .body p:first-child::first-letter{float:left;font-size:3.3rem;line-height:.9;padding:.25rem .5rem 0 0;color:var(--glow)}
.break{text-align:center;color:var(--glow);letter-spacing:.7em;margin:1.8rem 0}
.disclosure{border-top:1px solid var(--line);margin-top:2.6rem;padding-top:1rem}
.pager{display:flex;justify-content:space-between;gap:1rem;margin:2rem 0;font:0.9rem/1.4 -apple-system,"Helvetica Neue",Arial,sans-serif}
.card{border-top:1px solid var(--line);padding:1.5rem 0}
.card h2{font-size:1.45rem;line-height:1.25;margin:.1rem 0 .4rem;font-weight:normal}
.card p{margin:.4rem 0 .6rem;color:var(--soft)}
.hero{margin-bottom:1.5rem}
.hero p{color:var(--soft)}
.subscribe{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;margin:1.2rem 0 .5rem}
.subscribe code{word-break:break-all;color:var(--accent)}
footer.site{border-top:1px solid var(--line);margin-top:3rem;padding:1.4rem 0 3rem}
@media (max-width:520px){body{font-size:17px}h1{font-size:1.75rem}.herobox img{width:5.5rem;height:5.5rem}}
"""


def _esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def _fmt_date(iso: str) -> str:
    d = dt.datetime.fromisoformat(iso)
    return "%d %s" % (d.day, d.strftime("%B %Y"))


def story_html(story: str) -> str:
    scenes = [s.strip() for s in SCENE_BREAK_RE.split(story) if s.strip()]
    parts: List[str] = []
    for si, scene in enumerate(scenes):
        for para in re.split(r"\n\s*\n", scene):
            para = re.sub(r"\s*\n\s*", " ", para).strip()
            if para:
                parts.append("<p>%s</p>" % _esc(para))
        if si < len(scenes) - 1:
            parts.append('<p class="break" aria-hidden="true">&bull; &bull; &bull;</p>')
    return "\n".join(parts)


def published(cfg: Config) -> List[episodes.Episode]:
    """Episodes that have been published to the blog, oldest first."""
    eps = [e for e in episodes.list_all(cfg) if e.meta.get("blog")]
    return sorted(eps, key=lambda e: str(e.meta["blog"]["date"]))


def story_url(cfg: Config, slug: str) -> str:
    return "%s/stories/%s/" % (cfg.get("show", "base_url").rstrip("/"), slug)


def _layout(cfg: Config, title: str, description: str, body: str, root: str,
            canonical: str, og_type: str = "website") -> str:
    show = cfg.get("show", "title")
    cover = cfg.get("show", "cover_url")
    og_img = '<meta property="og:image" content="%s">' % _esc(cover) if cover and "example.com" not in cover else ""
    return """<!doctype html>
<html lang="%(lang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#101212">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:type" content="%(og_type)s">
<meta property="og:url" content="%(canonical)s">
%(og_img)s
<link rel="canonical" href="%(canonical)s">
<link rel="alternate" type="application/rss+xml" title="%(show)s stories" href="%(root)sblog.xml">
<link rel="alternate" type="application/rss+xml" title="%(show)s podcast" href="%(root)sfeed.xml">
<link rel="stylesheet" href="%(root)sstyle.css">
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="%(root)sindex.html">%(show)s</a>
<nav><a href="%(root)sindex.html">Stories</a><a href="%(root)sfeed.xml">Podcast feed</a></nav>
</div></header>
<main class="wrap">
%(body)s
</main>
<footer class="site"><div class="wrap small">%(disclosure)s</div></footer>
</body>
</html>
""" % {
        "lang": _esc(cfg.get("show", "language")), "title": _esc(title), "desc": _esc(description),
        "og_type": og_type, "canonical": _esc(canonical), "og_img": og_img, "root": root,
        "show": _esc(show), "body": body,
        "disclosure": "All stories on this site are written by an AI model and narrated by a synthetic voice.",
    }


def _reading_minutes(words: int) -> int:
    return max(1, round(words / 200.0))


def _tags_html(tags: List[str]) -> str:
    return '<div class="tags">%s</div>' % "".join("<span>%s</span>" % _esc(t) for t in tags) if tags else ""


def _story_page(cfg: Config, ep: episodes.Episode, prev: Optional[episodes.Episode],
                nxt: Optional[episodes.Episode], has_audio: bool) -> str:
    m = ep.meta
    root = "../../"
    words = int(m.get("word_count") or len(ep.story.split()))
    style = STYLES.get(str(m.get("style")), {}).get("label", "")
    meta_bits = [_fmt_date(str(m["blog"]["date"])), "%d min read" % _reading_minutes(words)]
    if style:
        meta_bits.append(style)

    player = ""
    if has_audio:
        mins = int(round(float(m.get("audio", {}).get("duration_seconds", 0)) / 60.0))
        label = "Listen to this story%s" % (" (%d min)" % mins if mins else "")
        player = ('<div class="player"><strong>%s</strong>'
                  '<audio controls preload="none" src="%sepisodes/%s.mp3"></audio>'
                  '<div class="small"><a href="%sepisodes/%s.mp3" download>Download MP3</a></div></div>'
                  % (_esc(label), root, _esc(ep.slug), root, _esc(ep.slug)))

    pager = []
    pager.append('<a href="../%s/index.html">&larr; %s</a>' % (_esc(prev.slug), _esc(prev.meta["title"])) if prev else "<span></span>")
    pager.append('<a href="../%s/index.html">%s &rarr;</a>' % (_esc(nxt.slug), _esc(nxt.meta["title"])) if nxt else "<span></span>")

    body = """<article>
<h1>%(title)s</h1>
<div class="meta">%(meta)s</div>
%(tags)s
<p class="lede">%(teaser)s</p>
%(player)s
<div class="body">
%(story)s
</div>
<p class="small disclosure">%(disclosure)s</p>
</article>
<nav class="pager">%(pager)s</nav>""" % {
        "title": _esc(m["title"]), "meta": " &middot; ".join(_esc(b) for b in meta_bits),
        "tags": _tags_html(list(m.get("tags", []))), "teaser": _esc(m["teaser"]), "player": player,
        "story": story_html(ep.story), "disclosure": _esc(cfg.get("show", "disclosure")),
        "pager": "".join(pager),
    }
    return _layout(cfg, "%s | %s" % (m["title"], cfg.get("show", "title")), str(m["teaser"]),
                   body, root, story_url(cfg, ep.slug), og_type="article")


def _index_page(cfg: Config, eps_newest_first: List[episodes.Episode], site: Path) -> str:
    base = cfg.get("show", "base_url").rstrip("/")
    cards = []
    for ep in eps_newest_first:
        m = ep.meta
        audio = (site / "episodes" / ("%s.mp3" % ep.slug)).exists()
        cards.append(
            '<div class="card"><div class="meta">%s%s</div>'
            '<h2><a href="stories/%s/index.html">%s</a></h2><p>%s</p>%s</div>' % (
                _esc(_fmt_date(str(m["blog"]["date"]))), " &middot; Audio available" if audio else "",
                _esc(ep.slug), _esc(m["title"]), _esc(m["teaser"]), _tags_html(list(m.get("tags", [])))))
    if not cards:
        cards.append('<p class="small">No stories published yet.</p>')

    has_cover = (site / "cover.jpg").exists()
    img = '<img src="cover.jpg" alt="%s cover art">' % _esc(cfg.get("show", "title")) if has_cover else ""
    body = """<section class="hero"><div class="herobox">%(img)s<div>
<h1>%(title)s</h1>
<p>%(desc)s</p>
</div></div>
<div class="subscribe small">Listen in your podcast app: add this feed URL<br><code>%(feed)s</code></div>
</section>
%(cards)s""" % {"img": img, "title": _esc(cfg.get("show", "title")), "desc": _esc(cfg.get("show", "description")),
                "feed": _esc(base + "/feed.xml"), "cards": "\n".join(cards)}
    return _layout(cfg, cfg.get("show", "title"), cfg.get("show", "description"), body, "", base + "/")


def _blog_feed(cfg: Config, eps_newest_first: List[episodes.Episode]) -> str:
    from xml.sax.saxutils import escape
    base = cfg.get("show", "base_url").rstrip("/")
    now = email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" '
           'xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
           "<title>%s</title>" % escape(cfg.get("show", "title")),
           "<link>%s/</link>" % escape(base),
           '<atom:link href="%s/blog.xml" rel="self" type="application/rss+xml"/>' % escape(base),
           "<description>%s</description>" % escape(cfg.get("show", "description")),
           "<language>%s</language>" % escape(cfg.get("show", "language")),
           "<lastBuildDate>%s</lastBuildDate>" % now]
    for ep in eps_newest_first:
        m = ep.meta
        pub = dt.datetime.fromisoformat(str(m["blog"]["date"]))
        if pub.tzinfo is None:
            pub = pub.astimezone()
        url = story_url(cfg, ep.slug)
        content = story_html(ep.story).replace("]]>", "]]&gt;")
        out += ["<item>", "<title>%s</title>" % escape(str(m["title"])), "<link>%s</link>" % escape(url),
                '<guid isPermaLink="true">%s</guid>' % escape(url),
                "<pubDate>%s</pubDate>" % email.utils.format_datetime(pub),
                "<description>%s</description>" % escape(str(m["teaser"])),
                "<content:encoded><![CDATA[%s]]></content:encoded>" % content, "</item>"]
    out += ["</channel></rss>", ""]
    return "\n".join(out)


def build(cfg: Config) -> int:
    """Regenerate the whole blog into the site folder. Returns the number of stories."""
    site = cfg.path("paths", "site")
    site.mkdir(parents=True, exist_ok=True)
    eps = published(cfg)

    (site / "style.css").write_text(CSS, encoding="utf-8")
    for i, ep in enumerate(eps):
        prev = eps[i - 1] if i > 0 else None
        nxt = eps[i + 1] if i < len(eps) - 1 else None
        has_audio = (site / "episodes" / ("%s.mp3" % ep.slug)).exists()
        page_dir = site / "stories" / ep.slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(_story_page(cfg, ep, prev, nxt, has_audio), encoding="utf-8")

    newest_first = list(reversed(eps))
    (site / "index.html").write_text(_index_page(cfg, newest_first, site), encoding="utf-8")
    (site / "blog.xml").write_text(_blog_feed(cfg, newest_first), encoding="utf-8")
    from .podcast import write_support_files
    write_support_files(cfg)
    return len(eps)


def mark_published(ep: episodes.Episode, cfg: Config) -> None:
    """Record the blog publication date once; later rebuilds keep the original date."""
    if not ep.meta.get("blog"):
        ep.meta["blog"] = {"date": dt.datetime.now().isoformat(timespec="seconds"),
                           "url": story_url(cfg, ep.slug)}
        ep.save()
