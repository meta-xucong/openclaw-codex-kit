"""Optional DashScope-compatible web-search adapter.

The adapter never reads platform configuration files. Credentials must be supplied
through DASHSCOPE_API_KEY and the endpoint can be changed with DASHSCOPE_BASE_URL.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


def web_search(query: str, model: str = "qwen-flash", max_words: int = 300) -> dict:
    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        return {"error": "缺少 DASHSCOPE_API_KEY；请通过当前用户的环境变量显式配置凭据。"}
    base_url = os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    prompt = (
        f"请使用可用的联网搜索能力查询，并根据检索到的信息进行总结。\n"
        f"总结不超过{max_words}字，写明来源名称和链接。\n用户问题：{query}"
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "enable_search": True,
        "search_options": {"search_strategy": "turbo"},
    }
    request = urllib.request.Request(
        base_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        choices = body.get("choices") or []
        content = ((choices[0].get("message") or {}).get("content") if choices else None)
        if not content:
            return {"error": "接口返回为空：未找到 message.content"}
        return {"success": True, "content": content}
    except urllib.error.HTTPError as error:
        return {"error": f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}"}
    except (urllib.error.URLError, TimeoutError) as error:
        return {"error": f"网络请求失败：{error}"}
    except (OSError, json.JSONDecodeError) as error:
        return {"error": f"请求或响应解析失败：{error}"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Optional web search adapter")
    parser.add_argument("query")
    parser.add_argument("--model", default="qwen-flash")
    parser.add_argument("--max-words", type=int, default=200)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = web_search(args.query, args.model, args.max_words)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif result.get("success"):
        print(result["content"])
    else:
        print(f"错误：{result.get('error', '未知错误')}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
