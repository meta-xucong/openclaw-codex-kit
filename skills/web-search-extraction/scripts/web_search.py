import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path


# 从用户目录下的 .openclaw/sosoclaw.json 加载 API_KEY
sosoclaw_json_path = Path.home() / ".openclaw" / "sosoclaw.json"
API_KEY = None

if sosoclaw_json_path.exists():
    try:
        with open(sosoclaw_json_path, "r", encoding="utf-8") as f:
            env_data = json.load(f)
            API_KEY = env_data.get("API_KEY")
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON in {sosoclaw_json_path}: {str(e)}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Failed to read {sosoclaw_json_path}: {str(e)}"}))
        sys.exit(1)
else:
    print(json.dumps({"error": f"{sosoclaw_json_path} not found"}))
    sys.exit(1)


def web_search(query: str, model: str = "qwen-flash", max_words: int = 300) -> dict:
    if not API_KEY:
        return {"error": f"API_KEY not found in {sosoclaw_json_path}"}

    url = "https://sosoclaw.canpan.net/api/llm/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    user_prompt = (
        f"请使用联网搜索功能查询，并根据检索到的信息进行总结。\n"
        f"输出要求：\n"
        f"1) 总结正文不超过{max_words}字。\n"
        f"2) 必须写明信息来源（尽量提供站点名+链接，如果没有就不写）：\n"
        f"   - 数据来源：...\n"
        f"用户提问：{query}"
    )

    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_prompt},
        ],
        "enable_search": True,
        "search_options": {
            "search_strategy": "turbo",
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req) as response:
            resp_json = json.loads(response.read().decode("utf-8"))

        choices = resp_json.get("choices") or []
        if not choices:
            return {"error": "接口返回为空：未找到 choices"}

        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            return {"error": "接口返回为空：未找到 message.content"}

        return {"success": True, "content": content}

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            return {"error": f"HTTP {e.code}：{body}"}
        except Exception:
            return {"error": f"HTTP 错误 {e.code}：{e.reason}"}
    except Exception as e:
        return {"error": f"请求失败：{str(e)}"}


def main() -> None:
    parser = argparse.ArgumentParser(description="联网搜索（Web Search）Skill")
    parser.add_argument("query", type=str, help="搜索关键词或问题")
    parser.add_argument("--model", type=str, default="qwen-flash", help="模型名称，例如 qwen-flash")
    parser.add_argument("--max-words", type=int, default=200, help="总结字数上限")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    result = web_search(args.query, model=args.model, max_words=args.max_words)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result.get("success"):
            print(result.get("content", ""))
        else:
            print(f"错误：{result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
