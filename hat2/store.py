"""記事データ (data/articles.json) の読み書き。"""
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "articles.json"


def load():
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save(articles, max_articles):
    articles = sorted(articles, key=lambda a: a["published"], reverse=True)[:max_articles]
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(articles, ensure_ascii=False, indent=1), encoding="utf-8")
    return articles
