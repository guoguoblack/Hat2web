"""data/articles.json から静的サイト (public/) を生成する。"""
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public"
JST = ZoneInfo("Asia/Tokyo")


def jst(iso, fmt="%Y年%-m月%-d日 %H:%M"):
    return datetime.fromisoformat(iso).astimezone(JST).strftime(fmt)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(config, articles):
    site = config["site"]
    categories = config["categories"]
    cat_map = {c["slug"]: c for c in categories}
    articles = [a for a in articles if a.get("relevant", True)]

    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape())
    env.filters["jst"] = jst
    now = datetime.now(timezone.utc).isoformat()
    common = dict(site=site, categories=categories, cat_map=cat_map, base=site["base_path"],
                  updated=now)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT / "static")

    by_cat = {c["slug"]: [a for a in articles if a["category"] == c["slug"]] for c in categories}
    tags = {}
    for a in articles:
        for t in a.get("tags", []):
            tags.setdefault(t, []).append(a)
    popular_tags = sorted(tags, key=lambda t: len(tags[t]), reverse=True)[:20]

    write(OUT / "index.html", env.get_template("index.html").render(
        **common, latest=articles[:12], by_cat=by_cat, tags=popular_tags, page="home"))
    for c in categories:
        write(OUT / "category" / c["slug"] / "index.html", env.get_template("list.html").render(
            **common, heading=f"{c['icon']} {c['name']}", items=by_cat[c["slug"]], page=c["slug"]))
    for t, items in tags.items():
        write(OUT / "tag" / t / "index.html", env.get_template("list.html").render(
            **common, heading=f"# {t}", items=items, page="tag"))
    for a in articles:
        related = [r for r in by_cat[a["category"]] if r["id"] != a["id"]][:5]
        write(OUT / "article" / a["id"] / "index.html", env.get_template("article.html").render(
            **common, a=a, related=related, page=a["category"]))
    write(OUT / "about" / "index.html", env.get_template("about.html").render(**common, page="about"))
    write(OUT / "feed.xml", env.get_template("feed.xml").render(**common, items=articles[:50]))
    write(OUT / "sitemap.xml", env.get_template("sitemap.xml").render(
        **common, items=articles, tag_names=list(tags)))
    print(f"  サイト生成: 記事 {len(articles)} 件 → {OUT}")
