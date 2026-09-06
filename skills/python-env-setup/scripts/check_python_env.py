#!/usr/bin/env python3
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

PREFERRED_MAJOR = 3
PREFERRED_MINOR = 13
WINDOWS_EMBED_VERSION = "3.13.2"
PYTHON_313_WINDOWS_EMBED_URL = f"https://www.python.org/ftp/python/{WINDOWS_EMBED_VERSION}/python-{WINDOWS_EMBED_VERSION}-embed-amd64.zip"
PYTHON_313_WINDOWS_X64_URL = "https://www.python.org/ftp/python/3.13.5/python-3.13.5-amd64.exe"
WINDOWS_SILENT_INSTALL_ARGS = ["/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0", "SimpleInstall=1", "Include_launcher=1"]
PATH_MARKER = "# Added by python-env-setup skill for Python"


@dataclass
class PythonMatch:
    command: str
    path: str
    version: str


@dataclass
class InstallAttempt:
    method: str
    command: List[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass
class PathUpdateResult:
    changed: bool
    method: str
    details: List[str]


def run_command(command: List[str], shell: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, shell=shell)


def parse_version(raw: str) -> Optional[Tuple[int, int, int]]:
    text = raw.strip()
    if text.lower().startswith("python "):
        text = text.split(" ", 1)[1]
    match = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        return None
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0)
    return major, minor, patch


def is_any_python_version(version: str) -> bool:
    parsed = parse_version(version)
    return bool(parsed and parsed[0] >= 2)


def is_preferred_version(version: str) -> bool:
    parsed = parse_version(version)
    return bool(parsed and parsed[0] == PREFERRED_MAJOR and parsed[1] == PREFERRED_MINOR)


def command_version(command_name: str, require_preferred: bool = False) -> Optional[PythonMatch]:
    path = shutil.which(command_name)
    if not path:
        return None
    result = run_command([path, "--version"])
    output = (result.stdout or result.stderr).strip()
    ok = is_preferred_version(output) if require_preferred else is_any_python_version(output)
    if result.returncode == 0 and ok:
        return PythonMatch(command=command_name, path=path, version=output)
    return None


def detect_python() -> Optional[PythonMatch]:
    for command_name in ["python", "python3", "python3.13"]:
        match = command_version(command_name)
        if match:
            return match
    return None


def preferred_command_ready() -> bool:
    system_name = platform.system().lower()
    if system_name == "windows":
        return command_version("python") is not None or command_version("python3") is not None or command_version("python3.13") is not None
    return command_version("python3") is not None or command_version("python3.13") is not None or command_version("python") is not None


def windows_candidate_dirs() -> List[str]:
    candidates: List[str] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    user_profile = os.environ.get("USERPROFILE")

    if local_app_data:
        candidates.extend(
            [
                os.path.join(local_app_data, "Programs", "Python", "Python313"),
                os.path.join(local_app_data, "Microsoft", "WindowsApps"),
            ]
        )
    if user_profile:
        candidates.append(os.path.join(user_profile, "Python313"))
    candidates.append("C:\\Python313")
    if program_files:
        candidates.append(os.path.join(program_files, "Python313"))
    if program_files_x86:
        candidates.append(os.path.join(program_files_x86, "Python313"))

    deduped: List[str] = []
    for item in candidates:
        if item not in deduped:
            deduped.append(item)
    return deduped


def detect_windows_python_anywhere() -> Optional[PythonMatch]:
    for command in (["where", "python"], ["where", "python3"], ["where", "py"]):
        result = run_command(command)
        if result.returncode == 0:
            for line in (result.stdout or "").splitlines():
                candidate = line.strip()
                if candidate.lower().endswith(("python.exe", "python3.exe", "py.exe")):
                    if candidate.lower().endswith("py.exe"):
                        version_result = run_command([candidate, "--version"])
                    else:
                        version_result = run_command([candidate, "--version"])
                    output = (version_result.stdout or version_result.stderr).strip()
                    if version_result.returncode == 0 and is_any_python_version(output):
                        return PythonMatch(command=os.path.splitext(os.path.basename(candidate))[0], path=candidate, version=output)

    for directory in windows_candidate_dirs():
        for exe_name in ["python.exe", "python3.exe", "python3.13.exe"]:
            candidate = os.path.join(directory, exe_name)
            if os.path.exists(candidate):
                version_result = run_command([candidate, "--version"])
                output = (version_result.stdout or version_result.stderr).strip()
                if version_result.returncode == 0 and is_any_python_version(output):
                    return PythonMatch(command=os.path.splitext(exe_name)[0], path=candidate, version=output)
    return None


def detect_macos_python_anywhere() -> Optional[PythonMatch]:
    for candidate in [
        "/opt/homebrew/bin/python3",
        "/opt/homebrew/bin/python3.13",
        "/usr/local/bin/python3",
        "/usr/local/bin/python3.13",
        "/usr/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13",
    ]:
        if os.path.exists(candidate):
            version_result = run_command([candidate, "--version"])
            output = (version_result.stdout or version_result.stderr).strip()
            if version_result.returncode == 0 and is_any_python_version(output):
                return PythonMatch(command=os.path.basename(candidate), path=candidate, version=output)
    return None


def detect_python_anywhere() -> Optional[PythonMatch]:
    system_name = platform.system().lower()
    direct = detect_python()
    if direct:
        return direct
    if system_name == "windows":
        return detect_windows_python_anywhere()
    if system_name == "darwin":
        return detect_macos_python_anywhere()
    return None


def detect_package_manager() -> Tuple[Optional[str], List[List[str]]]:
    system_name = platform.system().lower()

    if system_name == "darwin" and shutil.which("brew"):
        return "homebrew", [["brew", "install", "python@3.13"]]

    if system_name == "windows":
        commands: List[List[str]] = []
        if shutil.which("winget"):
            commands.append(["winget", "install", "-e", "--id", "Python.Python.3.13"])
        return "windows-installer", commands

    return None, []


def download_file(url: str, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with urllib.request.urlopen(url) as response, open(path, "wb") as handle:
        handle.write(response.read())
    return path


def install_windows_via_official_installer() -> InstallAttempt:
    installer_path = download_file(PYTHON_313_WINDOWS_X64_URL, ".exe")
    command = [installer_path, *WINDOWS_SILENT_INSTALL_ARGS]
    result = run_command(command)
    return InstallAttempt(
        method="official-installer",
        command=command,
        returncode=result.returncode,
        stdout=(result.stdout or "").strip(),
        stderr=(result.stderr or "").strip(),
    )


def enable_import_site(pth_file: str) -> bool:
    if not os.path.exists(pth_file):
        return False
    with open(pth_file, "r", encoding="utf-8") as handle:
        content = handle.read()
    new_content = content.replace("#import site", "import site")
    if new_content == content:
        return False
    with open(pth_file, "w", encoding="utf-8") as handle:
        handle.write(new_content)
    return True


def install_windows_via_embeddable_zip() -> List[InstallAttempt]:
    attempts: List[InstallAttempt] = []
    target_dir = "C:\\Python313"
    zip_path = download_file(PYTHON_313_WINDOWS_EMBED_URL, ".zip")
    attempts.append(
        InstallAttempt(
            method="embeddable-download",
            command=["download", PYTHON_313_WINDOWS_EMBED_URL, zip_path],
            returncode=0,
            stdout=f"Downloaded to {zip_path}",
            stderr="",
        )
    )

    try:
        os.makedirs(target_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(target_dir)
        attempts.append(
            InstallAttempt(
                method="embeddable-extract",
                command=["extract", zip_path, target_dir],
                returncode=0,
                stdout=f"Extracted to {target_dir}",
                stderr="",
            )
        )
    except Exception as exc:
        attempts.append(
            InstallAttempt(
                method="embeddable-extract",
                command=["extract", zip_path, target_dir],
                returncode=1,
                stdout="",
                stderr=str(exc),
            )
        )
        return attempts

    pth_file = os.path.join(target_dir, "python313._pth")
    changed = enable_import_site(pth_file)
    attempts.append(
        InstallAttempt(
            method="embeddable-enable-site",
            command=["patch", pth_file],
            returncode=0,
            stdout="Enabled import site" if changed else "import site already enabled",
            stderr="",
        )
    )
    return attempts


def install_python() -> Tuple[Optional[str], List[InstallAttempt]]:
    system_name = platform.system().lower()
    manager, command_groups = detect_package_manager()
    attempts: List[InstallAttempt] = []

    if system_name == "windows":
        for command in command_groups:
            result = run_command(command)
            attempts.append(
                InstallAttempt(
                    method="winget",
                    command=command,
                    returncode=result.returncode,
                    stdout=(result.stdout or "").strip(),
                    stderr=(result.stderr or "").strip(),
                )
            )
            if result.returncode == 0:
                return "winget", attempts

        embed_attempts = install_windows_via_embeddable_zip()
        attempts.extend(embed_attempts)
        if embed_attempts and all(item.returncode == 0 for item in embed_attempts):
            return "embeddable-zip", attempts

        attempts.append(install_windows_via_official_installer())
        if attempts[-1].returncode == 0:
            return "official-installer", attempts
        return "windows-fallback", attempts

    if not manager:
        return None, attempts

    for command in command_groups:
        result = run_command(command)
        attempts.append(
            InstallAttempt(
                method=manager,
                command=command,
                returncode=result.returncode,
                stdout=(result.stdout or "").strip(),
                stderr=(result.stderr or "").strip(),
            )
        )
        if result.returncode != 0:
            return manager, attempts

    return manager, attempts


def append_unique_line(file_path: str, line: str) -> bool:
    existing = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as handle:
            existing = handle.read()
    if line in existing:
        return False
    with open(file_path, "a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(f"\n{PATH_MARKER}\n{line}\n")
    return True


def ensure_macos_path() -> PathUpdateResult:
    details: List[str] = []
    candidate = detect_macos_python_anywhere()
    if not candidate:
        return PathUpdateResult(False, "macos", ["Unable to locate Python on disk."])

    bin_dir = os.path.dirname(candidate.path)
    if preferred_command_ready():
        return PathUpdateResult(False, "macos", ["Python is already available in PATH."])

    export_line = f'export PATH="{bin_dir}:$PATH"'
    target_files = [
        os.path.expanduser("~/.zprofile"),
        os.path.expanduser("~/.zshrc"),
        os.path.expanduser("~/.bash_profile"),
        os.path.expanduser("~/.bashrc"),
    ]

    for file_path in target_files:
        changed = append_unique_line(file_path, export_line)
        details.append(("Updated" if changed else "Already present") + f": {file_path}")
        if changed:
            return PathUpdateResult(True, "macos", details + [f"Added {bin_dir} to PATH."])

    return PathUpdateResult(False, "macos", details + ["PATH entry already existed in all candidate shell files."])


def find_windows_python_dirs() -> List[str]:
    found: List[str] = []
    any_python = detect_windows_python_anywhere()
    if any_python:
        found.append(os.path.dirname(any_python.path))

    for command in (["where", "python3.13"], ["where", "python3"], ["where", "python"], ["where", "py"]):
        result = run_command(command)
        if result.returncode == 0:
            for line in (result.stdout or "").splitlines():
                candidate = line.strip()
                if candidate.lower().endswith(("python.exe", "python3.exe", "python3.13.exe", "py.exe")):
                    directory = os.path.dirname(candidate)
                    if directory not in found:
                        found.append(directory)

    for directory in windows_candidate_dirs():
        python_exe = os.path.join(directory, "python.exe")
        python3_exe = os.path.join(directory, "python3.exe")
        python313_exe = os.path.join(directory, "python3.13.exe")
        if os.path.exists(python_exe) or os.path.exists(python3_exe) or os.path.exists(python313_exe):
            if directory not in found:
                found.append(directory)

    enriched: List[str] = []
    for directory in found:
        enriched.append(directory)
        scripts_dir = os.path.join(directory, "Scripts")
        if os.path.isdir(scripts_dir):
            enriched.append(scripts_dir)

    deduped: List[str] = []
    for directory in enriched:
        if directory not in deduped:
            deduped.append(directory)
    return deduped


def ensure_windows_path() -> PathUpdateResult:
    details: List[str] = []
    directories = find_windows_python_dirs()
    if not directories:
        return PathUpdateResult(False, "windows", ["Unable to locate Python installation directory."])

    current_user_path = os.environ.get("PATH", "")
    current_entries = current_user_path.split(os.pathsep) if current_user_path else []
    to_add = [item for item in directories if item and item not in current_entries]
    if not to_add:
        return PathUpdateResult(False, "windows", ["Python directories already present in PATH."])

    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell:
        joined = ";".join(to_add)
        ps_command = (
            "$old=[Environment]::GetEnvironmentVariable('Path','User');"
            f"$add='{joined}';"
            "$new=($old.TrimEnd(';') + ';' + $add).Trim(';');"
            "[Environment]::SetEnvironmentVariable('Path',$new,'User')"
        )
        result = run_command([powershell, "-NoProfile", "-Command", ps_command])
        details.append(f"PowerShell PATH update return code: {result.returncode}")
        if result.stderr:
            details.append(result.stderr.strip())
        if result.returncode == 0:
            details.append(f"Added to PATH: {', '.join(to_add)}")
            details.append("Refresh current shell with Machine+User PATH merge if immediate use is needed.")
            return PathUpdateResult(True, "windows", details)

    if shutil.which("setx"):
        new_path = current_user_path + (os.pathsep if current_user_path else "") + os.pathsep.join(to_add)
        result = run_command(["setx", "PATH", new_path])
        details.append(f"setx PATH return code: {result.returncode}")
        if result.stdout:
            details.append(result.stdout.strip())
        if result.stderr:
            details.append(result.stderr.strip())
        if result.returncode == 0:
            details.append(f"Added to PATH: {', '.join(to_add)}")
            details.append("Refresh current shell with Machine+User PATH merge if immediate use is needed.")
            return PathUpdateResult(True, "windows", details)

    return PathUpdateResult(False, "windows", details + [f"Failed to update PATH automatically. Candidate directories: {', '.join(to_add)}"])


def ensure_python_on_path() -> PathUpdateResult:
    system_name = platform.system().lower()
    if system_name == "darwin":
        return ensure_macos_path()
    if system_name == "windows":
        return ensure_windows_path()
    return PathUpdateResult(False, system_name, ["Unsupported platform for this skill."])


def build_result(install_requested: bool, repair_path: bool):
    system_name = platform.system().lower()
    if system_name not in {"darwin", "windows"}:
        return {
            "ok": False,
            "installed": False,
            "python": None,
            "installation_attempted": False,
            "message": "This skill only supports macOS and Windows.",
            "platform": system_name,
        }

    detected_anywhere = detect_python_anywhere()
    preferred_ready = preferred_command_ready()

    if detected_anywhere and repair_path and not preferred_ready:
        path_update = ensure_python_on_path()
        detected_after_repair = detect_python_anywhere()
        preferred_ready_after = preferred_command_ready()
        return {
            "ok": bool(detected_after_repair and preferred_ready_after),
            "installed": True,
            "python": asdict(detected_after_repair) if detected_after_repair else None,
            "installation_attempted": False,
            "path_repair_attempted": True,
            "path_update": asdict(path_update),
            "preferred_command_ready": preferred_ready_after,
            "message": "Python exists on disk; attempted to repair PATH so it can be called directly.",
        }

    if detected_anywhere:
        return {
            "ok": True,
            "installed": True,
            "python": asdict(detected_anywhere),
            "installation_attempted": False,
            "preferred_command_ready": preferred_ready,
            "path_repair_needed": not preferred_ready,
            "preferred_version": is_preferred_version(detected_anywhere.version),
            "message": (
                "Detected usable Python environment."
                if preferred_ready
                else "Detected Python environment, but the preferred command is not currently available in PATH."
            ),
        }

    manager, commands = detect_package_manager()
    result: Dict[str, object] = {
        "ok": False,
        "installed": False,
        "python": None,
        "installation_attempted": False,
        "detected_installer": manager,
        "suggested_commands": commands,
        "message": "No usable Python environment was found.",
        "platform": system_name,
    }
    if system_name == "windows":
        result["fallback_download"] = PYTHON_313_WINDOWS_EMBED_URL
        result["fallback_method"] = "embeddable-zip"

    if not install_requested:
        return result

    used_manager, attempts = install_python()
    result["installation_attempted"] = True
    result["install_method"] = used_manager
    result["attempts"] = [asdict(item) for item in attempts]

    path_update = ensure_python_on_path()
    result["path_update"] = asdict(path_update)

    detected_after = detect_python_anywhere()
    preferred_ready_after = preferred_command_ready()
    if detected_after:
        result.update(
            {
                "ok": preferred_ready_after,
                "installed": True,
                "python": asdict(detected_after),
                "preferred_command_ready": preferred_ready_after,
                "preferred_version": is_preferred_version(detected_after.version),
                "message": (
                    "Python installed successfully."
                    if preferred_ready_after
                    else "Python installed, but the current shell has not picked up PATH changes yet."
                ),
                "next_steps": [
                    "python --version",
                ],
            }
        )
        if system_name == "windows":
            result["next_steps"] = [
                "python --version",
                "$env:Path = [System.Environment]::GetEnvironmentVariable(\"Path\",\"Machine\") + ';' + [System.Environment]::GetEnvironmentVariable(\"Path\",\"User\")",
                "python --version",
            ]
        return result

    result["message"] = "Python installation did not complete successfully."
    if system_name == "windows":
        result["manual_admin_install"] = {
            "download": PYTHON_313_WINDOWS_X64_URL,
            "silent_args": WINDOWS_SILENT_INSTALL_ARGS,
            "notes": [
                "Primary Windows fallback is embeddable zip without UI.",
                "If even embeddable zip cannot satisfy the need, ask the user before retrying with administrator rights.",
                "Do not switch to elevated install silently.",
            ],
        }
    return result


def print_human_readable(result: dict) -> None:
    print(result["message"])
    if result.get("python"):
        print(f"Command: {result['python']['command']}")
        print(f"Path: {result['python']['path']}")
        print(f"Version: {result['python']['version']}")

    if "preferred_command_ready" in result:
        print(f"Preferred command available in PATH: {result['preferred_command_ready']}")
    if "preferred_version" in result:
        print(f"Preferred version (3.13): {result['preferred_version']}")

    installer = result.get("detected_installer")
    if installer:
        print(f"Detected installer strategy: {installer}")

    fallback_download = result.get("fallback_download")
    if fallback_download:
        print(f"Windows fallback installer: {fallback_download}")

    commands = result.get("suggested_commands") or []
    if commands:
        print("Suggested commands:")
        for command in commands:
            print("  " + " ".join(command))

    path_update = result.get("path_update")
    if path_update:
        print(f"PATH updated: {path_update.get('changed')}")
        for detail in path_update.get("details", []):
            print("  " + detail)

    attempts = result.get("attempts") or []
    if attempts:
        print("Install attempts:")
        for attempt in attempts:
            print("  " + " ".join(attempt["command"]) + f" -> {attempt['returncode']}")
            if attempt["stderr"]:
                print("    stderr: " + attempt["stderr"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or install Python environment.")
    parser.add_argument("--install", action="store_true", help="Attempt to install Python if missing.")
    parser.add_argument("--repair-path", action="store_true", help="Repair PATH if Python exists but the preferred command is not callable.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args()

    result = build_result(install_requested=args.install, repair_path=args.repair_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human_readable(result)

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
