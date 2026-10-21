#!/usr/bin/env python3
"""NovAI price index MCP server (stdio, zero dependencies).

Tools:
  - cheapest_models(category, limit, max_price)  -> cheapest models, with normalized prices
  - model_price(model)                           -> price lookup by name fragment
  - list_categories()                            -> available categories
Data: https://aiapi-pro.com/china-ai-leaderboard.json (official feed, updated daily).
"""
import json
import sys
import urllib.request

FEED = "https://aiapi-pro.com/china-ai-leaderboard.json"
_cache = {"data": None}


def load_feed():
    if _cache["data"] is None:
        req = urllib.request.Request(FEED, headers={"User-Agent": "novai-prices-mcp/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            _cache["data"] = json.load(r)
    return _cache["data"]


def all_models():
    feed = load_feed()
    return [m for cat in feed.get("categories", []) for m in cat.get("models", [])]


def fmt(m):
    name, prov = m.get("name", ""), m.get("provider", "")
    if m.get("normalized_unit") == "free":
        return f"- {name} ({prov}) — FREE — {m.get('url','')}"
    parts = []
    if m.get("price_per_1m_input") is not None:
        parts.append(f"${m['price_per_1m_input']}/1M in, ${m['price_per_1m_output']}/1M out")
    if m.get("cost_per_5s_est") is not None:
        parts.append(f"${m['cost_per_5s_est']} per 5s clip (est.)")
    if m.get("price_per_image") is not None:
        parts.append(f"${m['price_per_image']} per image")
    if not parts:
        parts.append(f"${m.get('price_usd')} {m.get('unit','')}")
    return f"- {name} ({prov}) — {'; '.join(parts)} — {m.get('url','')}"


def sort_key(m):
    if m.get("cost_per_5s_est") is not None:
        return float(m["cost_per_5s_est"])
    if m.get("price_per_image") is not None:
        return float(m["price_per_image"])
    if m.get("price_per_1m_input") is not None:
        # blended 1M input + 200K output for text models
        return float(m["price_per_1m_input"]) + 0.2 * float(m.get("price_per_1m_output") or 0)
    return float(m.get("price_usd") or 0)


def tool_cheapest(args):
    cat = (args.get("category") or "").lower()
    limit = int(args.get("limit") or 10)
    max_price = args.get("max_price")
    rows = [m for m in all_models() if not cat or cat in (m.get("category", "").lower())]
    if max_price is not None:
        rows = [m for m in rows if sort_key(m) <= float(max_price)]
    rows.sort(key=sort_key)
    rows = rows[:limit]
    text = "\n".join(fmt(m) for m in rows) or "No matching models."
    return (
        "Cheapest models on NovAI (provider list price, 0% platform markup).\n"
        "Text models are ranked by 1M input + 200K output; video by 5-second clip; image by generated image.\n\n"
        f"{text}\n\nFeed: {FEED}"
    )


def tool_price(args):
    q = (args.get("model") or "").lower().strip()
    if not q:
        return "Pass a model name fragment, e.g. {\"model\": \"deepseek\"}."
    hits = [m for m in all_models() if q in m.get("name", "").lower()]
    if not hits:
        return f"No model matched '{q}'."
    hits.sort(key=sort_key)
    return f"Matches for '{q}':\n" + "\n".join(fmt(m) for m in hits[:15])


def tool_categories(_args):
    feed = load_feed()
    cats = [f"- {c['category']} ({len(c.get('models', []))} models)" for c in feed.get("categories", [])]
    return "Categories:\n" + "\n".join(cats)


TOOLS = [
    {
        "name": "cheapest_models",
        "description": "List the cheapest Chinese AI models from NovAI's live price feed, ranked by a comparable cost unit (text: 1M input + 200K output; video: 5-second clip; image: per image).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Video, Image, Chat / LLM, Audio, 3D, Embedding"},
                "limit": {"type": "integer", "description": "max rows (default 10)"},
                "max_price": {"type": "number", "description": "only models whose comparable cost is at or below this USD figure"},
            },
        },
    },
    {
        "name": "model_price",
        "description": "Look up the NovAI list price of a model by name fragment (seedance, kimi, glm, qwen...).",
        "inputSchema": {"type": "object", "properties": {"model": {"type": "string"}}, "required": ["model"]},
    },
    {
        "name": "list_categories",
        "description": "List the model categories available in NovAI's price feed.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {"cheapest_models": tool_cheapest, "model_price": tool_price, "list_categories": tool_categories}


def reply(mid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": mid}
    msg["error" if error is not None else "result"] = error if error is not None else result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        mid, method = req.get("id"), req.get("method")
        params = req.get("params") or {}
        if method == "initialize":
            reply(mid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                        "serverInfo": {"name": "novai-prices", "version": "0.2.0"}})
        elif method == "tools/list":
            reply(mid, {"tools": TOOLS})
        elif method == "tools/call":
            handler = HANDLERS.get(params.get("name"))
            if not handler:
                reply(mid, error={"code": -32601, "message": "unknown tool"})
                continue
            try:
                reply(mid, {"content": [{"type": "text", "text": handler(params.get("arguments") or {})}], "isError": False})
            except Exception as e:
                reply(mid, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
        elif method.startswith("notifications/"):
            continue
        else:
            reply(mid, error={"code": -32601, "message": f"unsupported method: {method}"})


if __name__ == "__main__":
    main()
