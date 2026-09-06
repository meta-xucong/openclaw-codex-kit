"""Search the local, auditable skill catalog without network access."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"')
    return values


def _find_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if (root / "skills").is_dir():
            return root
        raise SystemExit(f"未找到 skills 目录：{root}")
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "manifest" / "imported-skills.txt").is_file():
            return parent
    raise SystemExit("无法定位能力包根目录，请使用 --root 指定。")


def search_skills(keyword: str, root: Path) -> list[dict[str, str]]:
    needle = keyword.casefold().strip()
    if not needle:
        raise SystemExit("keyword 不能为空")
    manifest = root / "manifest" / "imported-skills.txt"
    names = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    results = []
    for name in names:
        doc = root / "skills" / name / "SKILL.md"
        if not doc.is_file():
            continue
        meta = _frontmatter(doc)
        haystack = f"{name} {meta.get('name', '')} {meta.get('description', '')}".casefold()
        if needle in haystack:
            results.append({
                "name": meta.get("name") or name,
                "directory": name,
                "description": meta.get("description", ""),
                "skillFile": str(doc.relative_to(root)),
            })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the local Codex skill catalog")
    parser.add_argument("keyword", help="关键词")
    parser.add_argument("--root", help="能力包根目录；默认自动查找")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    result = search_skills(args.keyword, _find_root(args.root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if not result:
        print("未找到匹配的 Skill")
        return
    for index, item in enumerate(result, 1):
        print(f"{index}. {item['name']} ({item['directory']})\n   {item['description']}\n   状态由 dependencies.json 说明")


if __name__ == "__main__":
    main()
