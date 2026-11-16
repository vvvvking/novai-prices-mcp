<!-- mcp-name: io.github.vvvvking/novai-prices-mcp -->

# novai-prices-mcp

**Listed in the [official MCP Registry](https://registry.modelcontextprotocol.io) as `io.github.vvvvking/novai-prices`** — remote `streamable-http` endpoint: `https://aiapi-pro.com/api/mcp`?utm_source=github_readme&utm_medium=readme


An MCP server that answers one question well: **which Chinese AI model is cheapest for what I'm doing right now?**

It reads NovAI's live price feed (`https://aiapi-pro.com/china-ai-leaderboard.json`?utm_source=github_readme&utm_medium=readme) and normalizes every model into a comparable cost unit, because every provider quotes a different one:

| Modality | Unit the market quotes | Unit this server uses |
|---|---|---|
| Chat / LLM | per 1M input, per 1M output | **1M input + 200K output** (one large coding run) |
| Video | per second, per generation, per 1M tokens | **one 5-second clip** (token-billed models are converted) |
| Image | per image, per generation | **one image** |

Prices are the providers' list price passed through with a **1.0 multiplier and 0% platform markup** — the server reports the rate card, not a sales number.

## Tools

| Tool | What it does |
|---|---|
| `cheapest_models` | Cheapest models, optionally filtered by `category` and `max_price` |
| `model_price` | Price lookup by name fragment (`seedance`, `kimi`, `glm`, `qwen`…) |
| `list_categories` | Categories available in the feed |

## Run it

No dependencies beyond Python 3.9+:

```bash
python3 server.py
```

### Claude Desktop / Cline / any MCP client

```json
{
  "mcpServers": {
    "novai-prices": {
      "command": "python3",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

### Example session

```
→ tools/call cheapest_models {"category": "video", "limit": 3}
← CogVideoX-Flash (Zhipu AI) — FREE
  PixVerse C1 Video API (PixVerse) — $0.154 per 5s clip (est.)
  PixVerse V6.0 Video API (PixVerse) — $0.203 per 5s clip (est.)
```

```
→ tools/call cheapest_models {"category": "chat / llm", "limit": 3}
← GLM-4.7-Flash — FREE
  DeepSeek V4 Flash — $0.080/1M in, $0.170/1M out ($0.11 per 1M-in/200K-out run)
  GLM-5.3-Flash — $0.080/1M in, $0.280/1M out
```

## Why this exists

Price comparison for Chinese models is broken: one vendor quotes per second, another per token, a third per generation. Converting them by hand is error-prone, and every gateway's marketing page has an incentive to make its own numbers look good. This server just converts and sorts, and links to the machine-readable feed so the numbers can be checked.

## Data freshness

The feed is regenerated daily from the live model catalog. `generated_at` is included in the JSON; if the upstream feed is unreachable the tool returns an error rather than stale numbers.

## License

MIT

## Where it is listed

- Official MCP Registry: `io.github.vvvvking/novai-prices` (streamable HTTP)
- Glama connector: https://glama.ai/mcp/connectors/io.github.vvvvking/novai-prices — TDQS 3.6/5, Healthy
- `punkpeye/awesome-remote-mcp-servers` (Aggregators)
- mcpservers.org: https://mcpservers.org/servers/novai-prices-mcp (12 language versions)
- mcpub.dev: https://mcpub.dev/?q=novai
---

## Data source

The price data comes from NovAI's public price index: https://aiapi-pro.com/chinese-ai-api-pricing - one page per billing unit, generated from the same `/v1/models` endpoint the API serves. Every number this server returns can be checked against that page.

- Coverage: 114 models across 22 Chinese providers (measured from `GET https://aiapi-pro.com/v1/models`).
- Unit normalisation: prices are per million tokens, except media models (video / image / 3D / speech / music), which are billed per generation. The server keeps those in separate categories instead of mixing units.

## Update frequency

The index is regenerated weekly. `data/*.json` in this repository is the snapshot the server reads; if a price changes mid-week the snapshot is updated and **the commit timestamp on that file is the authoritative "as of" date**.

## Maintenance

Maintained by the NovAI team (https://aiapi-pro.com). Issues and pull requests are welcome for: wrong prices (include the vendor's own source URL), missing models, and normalisation errors. Expect an answer within a few days - this is a side project of the same team that runs the API, not a support channel.

## Not a promotion

The purpose of this server is to answer "which Chinese model is cheapest for this workload" with numbers that trace to a source and a date. It is not an advertisement: if the data is wrong, the correct outcome is a corrected dataset, not a better claim. Discounts and free tiers are reported because they change the answer, not because they are flattering.
