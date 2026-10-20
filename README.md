# Hat2ニュース

発達障害（ADHD・ASD・LDなど）のニュースを1日4回自動で集め、要約して公開するポータルサイトです。

```
RSS（Google News・厚労省など）
  → キーワードで絞り込み・重複を除く      hat2/collect.py
  → AI で要約・やさしい日本語・分類         hat2/summarize.py
  → 静的サイト（public/）を生成            hat2/build.py
  → GitHub Actions で1日4回実行し GitHub Pages に公開
```

## ローカルで動かす

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m hat2 update   # 収集 → 要約 → サイト生成
.venv/bin/python -m hat2 serve    # http://localhost:8000/Hat2web/ でプレビュー
.venv/bin/python -m hat2 build    # デザインだけ変えたときの再生成
```

AI 要約を使うには `export ANTHROPIC_API_KEY=sk-ant-...` を設定してから `update` します。
キーが無い場合は、キーワードでの分類だけで動きます（要約・やさしい日本語は付きません）。

## 公開手順（GitHub Pages）

1. GitHub にリポジトリを作って push する
2. Settings → Pages → Source を「GitHub Actions」にする
3. Settings → Secrets and variables → Actions に `ANTHROPIC_API_KEY` を登録する
4. Actions タブの「ニュース更新」→「Run workflow」で初回を実行する
5. https://guoguoblack.github.io/Hat2web/ で公開される
   （独自ドメインにしたら `config.yaml` の `base_path` を `"/"` に戻す）

## よく触るところ

| やりたいこと | 場所 |
|---|---|
| サイト名・キャッチコピー | `config.yaml` の `site` |
| ニュースの取得元を増やす | `config.yaml` の `feeds`（Google News は `q=` を変えるだけ） |
| 拾う／除外するキーワード | `include_keywords` / `exclude_keywords` |
| カテゴリ | `categories` |
| AI のモデル・費用の上限 | `ai.model` / `ai.max_per_run` |
| 更新の時刻 | `.github/workflows/update.yml` の `cron` |
| デザイン | `templates/` と `static/style.css` |
