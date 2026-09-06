"""Build the copyable, offline-auditable Codex capability pack.

The source tree is the editable catalog.  installer-pack/ is generated output and
contains only files that are safe to copy to another machine.  No network access,
credentials, caches, histories, or user artifacts are read by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "installer-pack"
PACK_ID = "codex-starter"
PACK_VERSION = "1.0.0"
STATUSES = {"ready", "requires-runtime", "requires-mcp", "requires-credential", "unsupported/disabled"}
TRANSIENT_NAMES = {".cache", ".git", ".codex", ".learnings", "drafts", "output", "__pycache__", "sessions", "memory", "logs", "createContent", "codex-data", "hooks", "node_modules", ".venv", "venv", ".ds_store", "thumbs.db", "desktop.ini"}
TRANSIENT_SUFFIXES = {".lock", ".db", ".sqlite", ".sqlite3"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_manifest(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    lines = text[4:end].splitlines()
    values: dict[str, str] = {}
    index = 0
    while index < len(lines):
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        key, raw = match.groups()
        raw = raw.strip()
        if key == "description" and raw in {"|", ">", "|-", ">-"}:
            chunks = []
            index += 1
            while index < len(lines) and (lines[index].startswith(" ") or not lines[index].strip()):
                chunks.append(lines[index].strip())
                index += 1
            values[key] = " ".join(item for item in chunks if item)
            continue
        values[key] = raw.strip('"').strip("'")
        index += 1
    return values


def parse_toml(path: Path) -> dict[str, str]:
    try:
        import tomllib

        return tomllib.loads(path.read_text(encoding="utf-8"))
    except ModuleNotFoundError:
        result: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r'^\s*(name|description|developer_instructions)\s*=\s*["\'](.*)["\']\s*$', line)
            if match:
                result[match.group(1)] = match.group(2)
        return result


def safe_copy_tree(source: Path, destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = set()
        for name in names:
            lower = name.casefold()
            if name in TRANSIENT_NAMES or lower in {item.casefold() for item in TRANSIENT_NAMES}:
                ignored.add(name)
            elif lower.endswith(tuple(s.casefold() for s in TRANSIENT_SUFFIXES)):
                ignored.add(name)
            elif lower.endswith("_tasks.json") or lower.endswith(".json.lock"):
                ignored.add(name)
            elif lower.endswith("-market.json"):
                ignored.add(name)
            elif lower == ".env" or lower.startswith(".env."):
                ignored.add(name)
            elif lower.endswith(("credentials.json", "secrets.json")):
                ignored.add(name)
        return ignored

    shutil.copytree(source, destination, ignore=ignore, dirs_exist_ok=True)


def component_dependency(raw: str, status: str, capabilities: list[str]) -> dict:
    text = str(raw)
    required = status not in {"ready", "unsupported/disabled"}
    if text.startswith("python>="):
        return {"type":"runtime","name":"Python","minVersion":text.split(">=",1)[1],"architecture":"x64","required":required,"offlineInstallerFilename":"python-3.x.x-amd64.exe","detection":"python --version or py -3 --version","silentArgs":"/quiet InstallAllUsers=0 PrependPath=1","restart":"recommended","license":"PSF License","source":"https://www.python.org/downloads/windows/","dependentCapabilities":capabilities}
    if text in {"python>=3.10 optional", "Python 3.10+"}:
        return {"type":"runtime","name":"Python","minVersion":"3.10","architecture":"x64","required":False,"offlineInstallerFilename":"python-3.x.x-amd64.exe","detection":"python --version or py -3 --version","silentArgs":"/quiet InstallAllUsers=0 PrependPath=1","restart":"recommended","license":"PSF License","source":"https://www.python.org/downloads/windows/","dependentCapabilities":capabilities}
    if text.startswith("python"):
        return {"type":"runtime","name":"Python package runtime","minVersion":"3.10","architecture":"x64","required":required,"offlineInstallerFilename":"python-3.x.x-amd64.exe","detection":"python --version","silentArgs":"/quiet InstallAllUsers=0 PrependPath=1","restart":"recommended","license":"PSF License","source":"https://www.python.org/downloads/windows/","dependentCapabilities":capabilities}
    if text in {"Windows PowerShell", "curl.exe or Invoke-RestMethod", "network"}:
        return {"type":"system","name":text,"minVersion":"Windows 10","architecture":"x64","required":required,"offlineInstallerFilename":None,"detection":"Get-Command curl.exe or Get-Command Invoke-RestMethod","silentArgs":None,"restart":"none","license":"Microsoft system component","source":"Windows 10/11","dependentCapabilities":capabilities}
    if text.endswith("-mcp") or text == "feishu-doc-mcp" or text.startswith("feishu-"):
        return {"type":"mcp","name":text,"minVersion":None,"architecture":"any","required":True,"offlineInstallerFilename":None,"detection":"MCP client lists the declared tools","silentArgs":None,"restart":"client reload","license":"user supplied","source":"user supplied MCP server","dependentCapabilities":capabilities}
    if text.endswith("_API_KEY") or text.endswith("_BASE_URL"):
        return {"type":"credential","name":text,"minVersion":None,"architecture":"any","required":True,"offlineInstallerFilename":None,"detection":f"environment variable {text} is non-empty","silentArgs":None,"restart":"client reload","license":"user supplied","source":"user environment or secret manager","dependentCapabilities":capabilities}
    if text in {"native-web-or-user-sources", "native-web-tool-or-user-sources"}:
        return {"type":"capability","name":text,"minVersion":None,"architecture":"any","required":False,"offlineInstallerFilename":None,"detection":"current Codex web tool or user-provided sources","silentArgs":None,"restart":"none","license":"current environment","source":"Codex or user supplied","dependentCapabilities":capabilities}
    if text in {"image-2-endpoint", "seedance-endpoint", "optional image endpoint"} or text.startswith("optional "):
        return {"type":"service","name":text,"minVersion":None,"architecture":"any","required":required,"offlineInstallerFilename":None,"detection":"endpoint configured by user","silentArgs":None,"restart":"none","license":"service provider terms","source":"user supplied","dependentCapabilities":capabilities}
    if "[" in text or text in {"pandas", "numpy", "matplotlib", "akshare", "openpyxl", "python-docx", "python-pptx", "pypdf", "pdfplumber", "reportlab", "html2text"}:
        package = text.split("[", 1)[0]
        return {"type":"python-package","name":package,"minVersion":"current supported release","architecture":"any","required":required,"offlineInstallerFilename":f"{package}-wheelhouse.zip","detection":f"python -c \"import {package.replace('-', '_')}\"","silentArgs":None,"restart":"none","license":"package license","source":"PyPI or approved offline wheelhouse","dependentCapabilities":capabilities}
    return {"type":"dependency","name":text,"minVersion":None,"architecture":"any","required":required,"offlineInstallerFilename":None,"detection":"manual check","silentArgs":None,"restart":"none","license":"verify before use","source":"user supplied","dependentCapabilities":capabilities}


def build_dependencies(audit: dict, agents: dict) -> dict:
    skills = []
    for item in audit["skills"]:
        deps = [component_dependency(dep, item["status"], item.get("capabilities", [])) for dep in item.get("dependencies", [])]
        skills.append({
            "id": item["id"],
            "path": f"skills/{item['id']}",
            "status": item["status"],
            "defaultEnabled": bool(item.get("defaultEnabled", False)),
            "dependencyTypes": sorted({dep["type"] for dep in deps}),
            "dependencies": deps,
            "dependentCapabilities": item.get("capabilities", []),
            "notes": item.get("notes", "")
        })
    agent_items = []
    for item in agents["agents"]:
        deps = [{"type":"skill","name":skill,"minVersion":None,"architecture":"any","required":True,"offlineInstallerFilename":None,"detection":f"skills/{skill}/SKILL.md exists","silentArgs":None,"restart":"Codex reload","license":"package license","source":"this pack","dependentCapabilities":[item["description"]]} for skill in item.get("skills", [])]
        agent_items.append({
            "id": item["id"], "file": f"agents/{item['file']}", "name": item["name"],
            "description": item["description"], "status": item["status"], "defaultEnabled": True,
            "dependencyTypes": ["skill"], "dependencies": deps, "dependentCapabilities":[item["description"]]
        })
    system = [
        {"type":"system","name":"Windows 10/11","minVersion":"10","architecture":"x64","required":True,"offlineInstallerFilename":None,"detection":"Get-CimInstance Win32_OperatingSystem","silentArgs":None,"restart":"none","license":"Microsoft","source":"Windows","dependentCapabilities":["installer"]},
        {"type":"runtime","name":"PowerShell","minVersion":"5.1","architecture":"x64","required":True,"offlineInstallerFilename":None,"detection":"$PSVersionTable.PSVersion","silentArgs":None,"restart":"none","license":"Microsoft","source":"Windows","dependentCapabilities":["installer"]},
        {"type":"runtime","name":"Git","minVersion":"2.x","architecture":"x64","required":False,"offlineInstallerFilename":"Git-*-64-bit.exe","detection":"git --version","silentArgs":"/VERYSILENT /NORESTART","restart":"optional","license":"GPL-2.0","source":"https://git-scm.com/download/win","dependentCapabilities":["deployment"]},
        {"type":"runtime","name":"Node.js","minVersion":"18","architecture":"x64","required":False,"offlineInstallerFilename":"node-v18+-x64.msi","detection":"node --version","silentArgs":"/qn /norestart","restart":"recommended","license":"Node.js license","source":"https://nodejs.org/en/download","dependentCapabilities":["future Node skills"]},
        {"type":"system","name":"curl.exe","minVersion":"Windows 10","architecture":"x64","required":False,"offlineInstallerFilename":None,"detection":"Get-Command curl.exe","silentArgs":None,"restart":"none","license":"Microsoft","source":"Windows component","dependentCapabilities":["weather"]}
    ]
    return {"schemaVersion":1,"id":PACK_ID,"version":PACK_VERSION,"policy":"No secrets, caches, history, databases, drafts or user content.","system":system,"skills":skills,"agents":agent_items}


def validate_sources(skill_names: list[str], audit: dict, agents: dict) -> None:
    expected = set(skill_names)
    seen_names: dict[str, str] = {}
    for skill_id in skill_names:
        doc = ROOT / "skills" / skill_id / "SKILL.md"
        metadata = frontmatter(doc)
        name = metadata.get("name", "").strip()
        description = metadata.get("description", "").strip()
        if name != skill_id:
            raise SystemExit(f"Skill name mismatch: {skill_id} has {name!r}")
        if not description:
            raise SystemExit(f"Skill description missing: {skill_id}")
        if name in seen_names:
            raise SystemExit(f"Duplicate skill name: {name} ({seen_names[name]}, {skill_id})")
        seen_names[name] = skill_id
    if len(seen_names) != 50:
        raise SystemExit(f"Expected 50 unique skill names, got {len(seen_names)}")
    known = set(seen_names)
    agent_names = set()
    for item in agents["agents"]:
        path = ROOT / "agents" / item["file"]
        if not path.is_file():
            raise SystemExit(f"Agent file missing: {item['file']}")
        parsed = parse_toml(path)
        for required in ("name", "description", "developer_instructions"):
            if not str(parsed.get(required, "")).strip():
                raise SystemExit(f"Agent field missing: {item['file']} -> {required}")
        if "model" in parsed or "mcp" in parsed:
            raise SystemExit(f"Agent contains an unnecessary lock or unsupported field: {item['file']}")
        if parsed["name"] != item["name"]:
            raise SystemExit(f"Agent catalog name mismatch: {item['file']}")
        if parsed["name"] in agent_names:
            raise SystemExit(f"Duplicate agent name: {parsed['name']}")
        agent_names.add(parsed["name"])
        text = f"{parsed['description']}\n{parsed['developer_instructions']}"
        for skill_id in re.findall(r"[a-z][a-z0-9]+(?:-[a-z0-9]+)+", text):
            if skill_id in known and skill_id not in item.get("skills", []):
                raise SystemExit(f"Agent dependency catalog incomplete: {item['file']} -> {skill_id}")
        for skill_id in item.get("skills", []):
            if skill_id not in known:
                raise SystemExit(f"Agent references missing skill: {item['file']} -> {skill_id}")
    forbidden_tokens = ["open" + "claw", "claw" + "dbot", "ran" + "claw"]
    forbidden = re.compile("|".join(re.escape(token) for token in forbidden_tokens), re.IGNORECASE)
    secret_like = re.compile(r"(?:sk-[A-Za-z0-9]{20,}|Bearer\\s+[A-Za-z0-9._-]{20,})")
    text_suffixes = {".md", ".py", ".js", ".ts", ".json", ".toml", ".ps1", ".sh", ".txt"}
    for path in [ROOT / "README.md", ROOT / "ENVIRONMENT-MCP-INVENTORY.md", ROOT / "agents", ROOT / "manifest", ROOT / "scripts", ROOT / "skills"]:
        paths = [path] if path.is_file() else [candidate for candidate in path.rglob("*") if candidate.is_file()]
        for candidate in paths:
            if candidate.name.casefold().endswith("-market.json") or candidate.suffix.lower() not in text_suffixes or any(part in TRANSIENT_NAMES for part in candidate.parts):
                continue
            text = candidate.read_text(encoding="utf-8")
            if forbidden.search(text):
                raise SystemExit(f"Legacy platform marker found: {candidate}")
            if secret_like.search(text):
                raise SystemExit(f"Secret-like token found: {candidate}")


def pack_files() -> list[Path]:
    return sorted(path for path in PACK.rglob("*") if path.is_file())


def build() -> dict:
    audit = read_json(ROOT / "manifest" / "skill-audit.json")
    agents = read_json(ROOT / "manifest" / "agent-audit.json")
    skill_names = read_manifest(ROOT / "manifest" / "imported-skills.txt")
    audit_names = [item["id"] for item in audit["skills"]]
    if len(skill_names) != 50 or set(skill_names) != set(audit_names):
        raise SystemExit(f"Skill audit mismatch: manifest={len(skill_names)}, audit={len(audit_names)}")
    if set(item["status"] for item in audit["skills"]) - STATUSES:
        raise SystemExit("Unknown compatibility status in skill audit")
    validate_sources(skill_names, audit, agents)
    if PACK.exists():
        if PACK.parent != ROOT or PACK.name != "installer-pack":
            raise SystemExit("Refusing to recreate an unexpected pack path")
        shutil.rmtree(PACK)
    (PACK / "skills").mkdir(parents=True)
    (PACK / "agents").mkdir(parents=True)
    (PACK / "mcp").mkdir(parents=True)
    (PACK / "manifest").mkdir(parents=True)
    for agent in sorted((ROOT / "agents").glob("*.toml")):
        shutil.copy2(agent, PACK / "agents" / agent.name)
    for name in skill_names:
        source = ROOT / "skills" / name
        if not (source / "SKILL.md").is_file():
            raise SystemExit(f"Missing SKILL.md: {name}")
        safe_copy_tree(source, PACK / "skills" / name)
    for relative in ["README.md", "ENVIRONMENT-MCP-INVENTORY.md"]:
        shutil.copy2(ROOT / relative, PACK / relative)
    for relative in ["imported-skills.txt", "agents.txt", "agent-catalog.md", "source-notes.md", "skill-audit.json", "agent-audit.json"]:
        shutil.copy2(ROOT / "manifest" / relative, PACK / "manifest" / relative)
    write_json(PACK / "mcp" / "servers.json", read_json(ROOT / "manifest" / "mcp-inventory.json"))
    (PACK / "mcp" / "README.md").write_text(
        "# MCP templates\n\nThis directory contains inventory-only templates. Add real server configuration outside the pack.\n",
        encoding="utf-8", newline="\n"
    )
    for template in (ROOT / "manifest").glob("*.template.*"):
        shutil.copy2(template, PACK / "mcp" / template.name)
    default_skills = [item["id"] for item in audit["skills"] if item.get("defaultEnabled")]
    default_agents = [f"agents/{item['file']}" for item in agents["agents"]]
    pack_manifest = {
        "schemaVersion": 1,
        "id": PACK_ID,
        "version": PACK_VERSION,
        "compatibleCodex": {"agentFormat":"TOML with name/description/developer_instructions", "skillRoot":"%USERPROFILE%\\.agents\\skills", "agentRoot":"%USERPROFILE%\\.codex\\agents", "windows":["10","11"]},
        "statuses": sorted(STATUSES),
        "defaultEnabled": {"skills": default_skills, "agents": default_agents},
        "sourcePolicy": {"noSecrets":True,"noUserContent":True,"noRuntimeCache":True,"ownedFilesOnly":True},
        "extensionContract": {"skill":"add manifest entry and skills/<id>/SKILL.md; rerun builder","agent":"add agents/<id>.toml and agent-audit entry; rerun builder","mcp":"add mcp inventory entry and a template; do not put secrets in pack"}
    }
    write_json(PACK / "pack.json", pack_manifest)
    write_json(PACK / "dependencies.json", build_dependencies(audit, agents))
    manifest = []
    for path in pack_files():
        relative = path.relative_to(PACK).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append({"path":relative,"sha256":digest,"bytes":path.stat().st_size,"owned":True})
    write_json(PACK / "file-manifest.json", {"schemaVersion":1,"id":PACK_ID,"version":PACK_VERSION,"files":manifest})
    return {"skills":len(skill_names),"agents":len(default_agents),"defaultSkills":len(default_skills),"files":len(manifest)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="build the pack and print a summary")
    args = parser.parse_args()
    result = build()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
