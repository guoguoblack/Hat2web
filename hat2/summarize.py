"""記事に要約・やさしい日本語・カテゴリ・タグを付ける。

ANTHROPIC_API_KEY があれば Claude で、無ければキーワードルールで処理する。
"""
import json
import os

TAGS = {
    "ADHD": ["ADHD", "注意欠如"],
    "ASD": ["自閉", "ASD", "アスペルガー"],
    "LD": ["学習障害", "限局性学習症", "ディスレクシア", "LD"],
    "特別支援教育": ["特別支援"],
    "合理的配慮": ["合理的配慮"],
    "グレーゾーン": ["グレーゾーン"],
    "大人の発達障害": ["大人の発達障害", "大人のADHD"],
    "ニューロダイバーシティ": ["ニューロダイバーシティ"],
}

SYSTEM = """あなたは発達障害（ADHD・ASD・LDなど）専門ニュースサイト「{site}」の編集者です。
渡されたニュースのタイトルと抜粋だけを根拠に、各記事を整理してください。

- relevant: 発達障害に関係する記事なら true。単語が偶然含まれるだけ、広告、無関係な話題なら false。
- category: 次から最も合うものを1つ: {cats}
- tags: 2〜4個。例: ADHD, ASD, LD, 大人の発達障害, 子ども, 就労, 教育, 医療, 制度, 研究
- summary: 要点を1〜3個の短い文で。抜粋に書かれていない事実や数字は絶対に足さない。情報が少なければ1文でよい。
- easy: 小学校高学年でも読める「やさしい日本語」で1〜2文。むずかしい言葉は言いかえる。

当事者や家族が読みます。「治る」「〜のせい」など、偏見を助長する言い方は避け、中立的に書いてください。"""


def rule_based(article, categories):
    text = article["title"] + " " + article["snippet"]
    article["category"] = next(
        (c["slug"] for c in categories if any(k in text for k in c["keywords"])),
        categories[-1]["slug"],
    )
    article["tags"] = [tag for tag, words in TAGS.items() if any(w in text for w in words)]
    snippet = article["snippet"]
    if snippet and article["title"][:20] not in snippet:
        article["summary"] = [snippet[:140] + ("…" if len(snippet) > 140 else "")]
    else:
        article["summary"] = []
    article["easy"] = ""
    article["relevant"] = True
    article["ai"] = False
    return article


def schema(slugs):
    item = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "relevant": {"type": "boolean"},
            "category": {"type": "string", "enum": slugs},
            "tags": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "array", "items": {"type": "string"}},
            "easy": {"type": "string"},
        },
        "required": ["id", "relevant", "category", "tags", "summary", "easy"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"items": {"type": "array", "items": item}},
        "required": ["items"],
        "additionalProperties": False,
    }


def ai_batch(client, batch, config):
    categories = config["categories"]
    slugs = [c["slug"] for c in categories]
    payload = [
        {"id": a["id"], "title": a["title"], "source": a["source"], "snippet": a["snippet"]}
        for a in batch
    ]
    model = config["ai"]["model"]
    # Haiku には fallbacks が無い（付けると 400）。それ以外は断られたら別モデルで再実行させる
    extra = {} if model.startswith("claude-haiku") else {
        "betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    response = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        **extra,
        output_config={
            "effort": config["ai"]["effort"],
            "format": {"type": "json_schema", "schema": schema(slugs)},
        },
        system=SYSTEM.format(
            site=config["site"]["name"],
            cats=", ".join(f"{c['slug']}({c['name']})" for c in categories),
        ),
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    if response.stop_reason != "end_turn":
        raise ValueError(f"stop_reason={response.stop_reason}")
    text = "".join(b.text for b in response.content if b.type == "text")
    results = {r["id"]: r for r in json.loads(text)["items"]}
    for a in batch:
        r = results.get(a["id"])
        if r is None:
            rule_based(a, categories)
            continue
        a.update(relevant=r["relevant"], category=r["category"], tags=r["tags"][:4],
                 summary=r["summary"][:3], easy=r["easy"], ai=True)


def summarize(articles, config):
    categories = config["categories"]
    use_ai = config["ai"]["enabled"] and (
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )
    if not use_ai:
        print("  AI なし（ANTHROPIC_API_KEY 未設定）: キーワードで分類します")
        return [rule_based(a, categories) for a in articles]

    import anthropic

    client = anthropic.Anthropic()
    limit = config["ai"]["max_per_run"]
    targets, rest = articles[:limit], articles[limit:]
    for i in range(0, len(targets), 10):
        batch = targets[i:i + 10]
        try:
            ai_batch(client, batch, config)
            print(f"  AI 要約: {len(batch)} 件")
        except anthropic.RateLimitError:
            print("  ! レート制限: 残りはキーワードで分類します")
            rest = targets[i:] + rest
            break
        except (anthropic.APIStatusError, anthropic.APIConnectionError, ValueError) as e:
            print(f"  ! AI 失敗 ({e}): このまとまりはキーワードで分類します")
            for a in batch:
                rule_based(a, categories)
    for a in rest:
        rule_based(a, categories)
    return articles
