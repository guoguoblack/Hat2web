"""RSS からニュースを集め、キーワードで絞り込む。"""
import hashlib
import html
import re
from datetime import datetime, timedelta, timezone

import feedparser

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
IMAGE_RE = re.compile(r"^[(（＜<]?\s*画像\s*\d+\s*/\s*\d+\s*[)）＞>]?\s*")
# 重複判定用: 末尾の（媒体名）や「｜概要｜ニュース」を外し、記号を除いた先頭30文字で比べる
TAIL_RE = re.compile(r"\s*([（(][^（()）]*[)）]|[|｜].*)$")
PUNCT_RE = re.compile(r"[\s　「」『』【】、。・!?！？“”\"'…:：]")


def clean(text):
    text = html.unescape(TAG_RE.sub(" ", text or ""))
    return SPACE_RE.sub(" ", text).strip()


def normalize_title(title, source):
    # Google News はタイトル末尾に「 - 媒体名」が付くので外す
    if source and title.endswith(" - " + source):
        title = title[: -len(source) - 3]
    # 「＜画像4 / 55＞」「(画像2/9)」のような先頭の飾りを外す
    title = IMAGE_RE.sub("", title)
    return title.strip()


def make_id(title):
    key = PUNCT_RE.sub("", TAIL_RE.sub("", title))[:30]
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def entry_time(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def contains_any(text, words):
    lower = text.lower()
    return any(w.lower() in lower for w in words)


def fetch_feed(feed):
    parsed = feedparser.parse(feed["url"], agent="Hat2NewsBot/1.0 (+https://example.com)")
    if parsed.bozo and not parsed.entries:
        print(f"  ! {feed['name']}: 取得失敗 ({parsed.bozo_exception})")
        return []
    items = []
    for e in parsed.entries:
        source = e.get("source", {}).get("title") or parsed.feed.get("title", feed["name"])
        title = normalize_title(clean(e.get("title", "")), source)
        if not title:
            continue
        items.append({
            "id": make_id(title),
            "title": title,
            "link": e.get("link", ""),
            "source": source,
            "published": entry_time(e).isoformat(),
            "snippet": clean(e.get("summary", ""))[:600],
        })
    print(f"  - {feed['name']}: {len(items)} 件")
    return items


def collect(config, existing):
    known = {a["id"] for a in existing}
    cutoff = datetime.now(timezone.utc) - timedelta(days=config["storage"]["max_age_days"])
    new = {}
    for feed in config["feeds"]:
        for item in fetch_feed(feed):
            text = item["title"] + " " + item["snippet"]
            if item["id"] in known or item["id"] in new:
                continue
            if datetime.fromisoformat(item["published"]) < cutoff:
                continue
            if not contains_any(text, config["include_keywords"]):
                continue
            if contains_any(text, config["exclude_keywords"]):
                continue
            item["fetched"] = datetime.now(timezone.utc).isoformat()
            new[item["id"]] = item
    return list(new.values())
