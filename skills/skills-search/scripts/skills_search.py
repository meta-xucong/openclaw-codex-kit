import sys
import json
import argparse
import urllib.parse
import urllib.request
import urllib.error


def _safe_str(v):
    if v is None:
        return None
    if isinstance(v, str):
        return v
    return str(v)


def search_skills(keyword: str):
    if not isinstance(keyword, str) or not keyword.strip():
        return {"error": "keyword 不能为空"}

    base_url = "https://sosoclaw.canpan.net/api/skills/search"
    params = {
        "keyword": keyword,
    }

    query = urllib.parse.urlencode(params)
    url = f"{base_url}?{query}"

    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "skills-search/1.0 (+python urllib)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req) as response:
            raw = response.read()
            charset = None
            try:
                charset = response.info().get_content_charset()
            except Exception:
                charset = None

            decoded_text = None
            if charset:
                try:
                    decoded_text = raw.decode(charset)
                except Exception:
                    decoded_text = None

            if decoded_text is None:
                for enc in ("utf-8", "gb18030"):
                    try:
                        decoded_text = raw.decode(enc)
                        break
                    except Exception:
                        decoded_text = None

            if decoded_text is None:
                decoded_text = raw.decode("utf-8", errors="replace")

            resp_json = json.loads(decoded_text)

        records = None

        # 兼容两种接口返回：
        # 1) 标准包裹结构：{"code":200,"message":"...","data":{"page":{"records":[...]}}}
        # 2) 直接返回列表：[ {...}, {...} ]
        if isinstance(resp_json, list):
            records = resp_json
        elif isinstance(resp_json, dict):
            code = resp_json.get("code")
            if code is not None and code != 200:
                return {
                    "error": f"接口返回失败：{_safe_str(resp_json.get('message')) or 'unknown'}",
                    "code": code,
                    "response": resp_json,
                    "requestUrl": url,
                }

            data = resp_json.get("data")
            # 不分页接口：data 可能直接是 list
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # 常见字段：records/list/items
                for k in ("records", "list", "items"):
                    v = data.get(k)
                    if isinstance(v, list):
                        records = v
                        break

                # 分页接口：data.page.records
                if records is None:
                    page_obj = data.get("page")
                    if isinstance(page_obj, dict):
                        rec = page_obj.get("records")
                        if isinstance(rec, list):
                            records = rec

        if records is None:
            return {
                "error": "接口返回结构无法解析（未找到 records 列表）",
                "response": resp_json,
                "requestUrl": url,
            }

        items = []
        for r in records:
            if not isinstance(r, dict):
                continue
            items.append(
                {
                    "slug": _safe_str(r.get("slug")) or "",
                    "intro": _safe_str(r.get("intro")) or "",
                    "title": _safe_str(r.get("title")) or "",
                    "logo": _safe_str(r.get("logo")),
                    "description": _safe_str(r.get("description")) or "",
                    "url": _safe_str(r.get("packageUrl")) or "",
                }
            )

        return items

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            return {"error": f"HTTP {e.code}：{body}"}
        except Exception:
            return {"error": f"HTTP 错误 {e.code}：{e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"网络错误：{e.reason}"}
    except Exception as e:
        return {"error": f"请求失败：{str(e)}"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Skills 市场搜索（skills-search）")
    parser.add_argument("keyword", type=str, help="搜索关键词，例如：图像生成 / 视频生成")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    result = search_skills(args.keyword)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
        return

    if isinstance(result, dict) and result.get("error"):
        print(f"错误：{result.get('error')}")
        sys.exit(1)

    items = result or []
    if not items:
        print("未找到匹配的 Skills")
        return

    for i, item in enumerate(items, start=1):
        title = item.get("title") if isinstance(item, dict) else ""
        slug = item.get("slug") if isinstance(item, dict) else ""
        desc = item.get("description") if isinstance(item, dict) else ""
        url = item.get("url") if isinstance(item, dict) else ""
        slug_text = f"（{slug}）" if slug else ""
        print(f"{i}. {title}{slug_text}\n   {desc}\n   安装地址：{url}")


if __name__ == "__main__":
    main()
