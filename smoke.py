"""Smoke test the price MCP server over stdio (initialize -> tools/list -> tools/call)."""
import json
import subprocess
import sys

SERVER = r'C:\Users\32065\Documents\deepseek-harness\default-workspace\novai-marketing\mcp-prices\server.py'

reqs = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "cheapest_models", "arguments": {"category": "video", "limit": 5}}},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
     "params": {"name": "model_price", "arguments": {"model": "kimi"}}},
]

payload = "\n".join(json.dumps(r) for r in reqs) + "\n"
p = subprocess.run([sys.executable, SERVER], input=payload.encode(), capture_output=True, timeout=120)
print('returncode:', p.returncode)
if p.stderr:
    print('stderr:', p.stderr.decode()[:400])
for line in p.stdout.decode().splitlines():
    d = json.loads(line)
    if d.get('id') == 1:
        print('initialize ->', d['result']['serverInfo'])
    elif d.get('id') == 2:
        print('tools:', [t['name'] for t in d['result']['tools']])
    else:
        txt = d['result']['content'][0]['text']
        print(f"--- id {d['id']} ---")
        print(txt[:500])
