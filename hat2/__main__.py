"""使い方:
  python -m hat2 update   # 収集 → 要約 → サイト生成（定期実行はこれ）
  python -m hat2 build    # 保存済みデータからサイトだけ作り直す
  python -m hat2 serve    # http://localhost:8000 でプレビュー
"""
import functools
import http.server
import sys
from pathlib import Path

import yaml

from . import build, collect, store, summarize

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def update(config):
    existing = store.load()
    print("ニュースを収集中…")
    new = collect.collect(config, existing)
    print(f"  新着候補: {len(new)} 件")
    if new:
        summarize.summarize(new, config)
        kept = [a for a in new if a["relevant"]]
        print(f"  掲載: {len(kept)} 件 / 除外: {len(new) - len(kept)} 件")
    articles = store.save(existing + new, config["storage"]["max_articles"])
    build.build(config, articles)


def serve(config):
    base = config["site"]["base_path"]

    class Handler(http.server.SimpleHTTPRequestHandler):
        # 本番と同じ URL（/Hat2web/...）で見られるよう、base_path を外して public/ から返す
        def translate_path(self, path):
            if base != "/" and path.startswith(base):
                path = "/" + path[len(base):]
            return super().translate_path(path)

    handler = functools.partial(Handler, directory=str(build.OUT))
    print(f"http://localhost:8000{base} を開いてください（Ctrl+C で終了）")
    http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "update"
    config = load_config()
    if command == "update":
        update(config)
    elif command == "build":
        build.build(config, store.load())
    elif command == "serve":
        serve(config)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
