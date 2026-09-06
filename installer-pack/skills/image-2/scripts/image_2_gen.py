import argparse
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


IMAGE_2_API_BASE_URL = os.environ.get("IMAGE_2_API_BASE_URL", "").strip().rstrip("/")
IMAGE_GENERATION_ASYNC_URL = f"{IMAGE_2_API_BASE_URL}/api/llm/openai/v1/images/generations"
IMAGE_EDIT_ASYNC_URL = f"{IMAGE_2_API_BASE_URL}/api/llm/openai/v1/images/edits"
IMAGE_TASKS_BASE_URL = f"{IMAGE_2_API_BASE_URL}/api/llm/openai/v1/images/tasks"
DEFAULT_MODEL = os.environ.get("IMAGE_2_MODEL", "custom-image-2-vip").strip()
SUPPORTED_SIZE_PRESETS = {
    "1:1": "2048x2048",
    "2:3": "1360x2048",
    "3:2": "2048x1360",
    "3:4": "1536x2048",
    "4:3": "2048x1536",
    "4:5": "1632x2048",
    "5:4": "2048x1632",
    "9:16": "1152x2048",
    "16:9": "2048x1152",
    "21:9": "2048x864",
}
SUPPORTED_SIZES = set(SUPPORTED_SIZE_PRESETS.values())

TASK_SUCCESS_STATUSES = {"completed", "complete", "success", "succeeded"}
TASK_FAILURE_STATUSES = {"failed", "failure", "error", "canceled", "cancelled", "expired"}


def env_float(name, default):
    try:
        return float(str(os.environ.get(name) or "").strip())
    except (TypeError, ValueError):
        return float(default)


TASK_POLL_INTERVAL = max(env_float("IMAGE_2_TASK_POLL_INTERVAL", 3), 1)
TASK_POLL_TIMEOUT = max(env_float("IMAGE_2_TASK_POLL_TIMEOUT", 600), 30)


API_KEY = str(
    os.environ.get("IMAGE_2_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or ""
).strip()
def request_json(url, method="GET", headers=None, payload=None, timeout=600):
    body = None
    if payload is not None:
        if isinstance(payload, (dict, list)):
            body = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, str):
            body = payload.encode("utf-8")
        else:
            body = payload

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers or {},
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        message = f"HTTP Error {error.code}: {error.reason}"
        try:
            error_body = error.read().decode("utf-8")
            parsed = json.loads(error_body) if error_body else {}
            if isinstance(parsed, dict):
                message = parsed.get("error", {}).get("message") if isinstance(parsed.get("error"), dict) else None
                message = message or parsed.get("msg") or parsed.get("message") or f"HTTP Error {error.code}: {error.reason}"
        except Exception:
            pass
        raise RuntimeError(message) from error
    except urllib.error.URLError as error:
        raise RuntimeError(str(error.reason or error)) from error


def resolve_file_mime_type(file_path=""):
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    extension = str(Path(file_path).suffix or "").strip().lower()
    if extension == ".jpg":
        return "image/jpeg"
    if extension == ".png":
        return "image/png"
    if extension == ".webp":
        return "image/webp"
    if extension == ".svg":
        return "image/svg+xml"
    if extension == ".gif":
        return "image/gif"
    return "application/octet-stream"


def guess_image_extension(image_bytes):
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return ".webp"
    if image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        return ".gif"
    return ".png"


def b64_image_to_tempfile(b64_json):
    if not b64_json:
        raise RuntimeError("响应中缺少 b64_json")

    image_bytes = base64.b64decode(str(b64_json), validate=False)
    extension = guess_image_extension(image_bytes)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    try:
        temp_file.write(image_bytes)
        temp_file.flush()
        return temp_file.name
    finally:
        temp_file.close()


def build_image_auth_headers(content_type=None, agent_id=None):
    normalized_agent_id = str(agent_id or "").strip()
    if not normalized_agent_id:
        raise RuntimeError("请求 image-2 时必须提供 agent_id")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "agent-id": normalized_agent_id,
        "X-Async": True
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def normalize_task_status(task):
    if not isinstance(task, dict):
        return ""
    return str(task.get("status") or "").strip().lower()


def extract_task_error(task):
    if not isinstance(task, dict):
        return "异步任务失败"
    for key in ("error", "message", "msg"):
        value = task.get(key)
        if isinstance(value, dict):
            nested = value.get("message") or value.get("msg")
            if nested:
                return str(nested)
        elif value:
            return str(value)
    result = task.get("result")
    if isinstance(result, dict):
        error = result.get("error")
        if isinstance(error, dict) and (error.get("message") or error.get("msg")):
            return str(error.get("message") or error.get("msg"))
        if isinstance(error, str) and error:
            return error
    return f"异步任务失败（status={task.get('status')}）"


def submit_image_task(url, payload, content_type="application/json", agent_id=None):
    response_json = request_json(
        url,
        method="POST",
        headers=build_image_auth_headers(content_type=content_type, agent_id=agent_id),
        payload=payload,
        timeout=120,
    )
    # 检查是否为同步响应（直接返回 data[].b64_json）
    data_list = response_json.get("data")
    if isinstance(data_list, list) and len(data_list) > 0:
        first_item = data_list[0]
        if isinstance(first_item, dict) and first_item.get("b64_json"):
            print(f"同步响应，直接处理 b64_json...", file=sys.stderr)
            return "__sync_response__"
    task_id = str(response_json.get("task_id") or response_json.get("id") or "").strip()
    if not task_id:
        brief = json.dumps(response_json, ensure_ascii=False)[:300]
        raise RuntimeError(f"异步任务创建失败，响应缺少 task_id: {brief}")
    if normalize_task_status(response_json) in TASK_FAILURE_STATUSES:
        raise RuntimeError(extract_task_error(response_json))
    print(f"异步任务已创建: {task_id}，等待生成完成...", file=sys.stderr)
    return task_id


def wait_for_image_task(task_id, agent_id=None):
    poll_url = f"{IMAGE_TASKS_BASE_URL}/{task_id}"
    headers = build_image_auth_headers(agent_id=agent_id)
    started = time.monotonic()
    deadline = started + TASK_POLL_TIMEOUT
    last_status = ""
    last_report = -15.0

    while True:
        task = request_json(poll_url, method="GET", headers=headers, timeout=60)
        status = normalize_task_status(task)
        if status in TASK_SUCCESS_STATUSES:
            print(f"图片生成完成: {task_id}", file=sys.stderr)
            return task
        if status in TASK_FAILURE_STATUSES:
            raise RuntimeError(extract_task_error(task))

        elapsed = time.monotonic() - started
        if time.monotonic() >= deadline:
            raise RuntimeError(f"等待图片生成超时（{int(TASK_POLL_TIMEOUT)} 秒），task_id={task_id}")
        if status != last_status or elapsed - last_report >= 15:
            print(f"图片生成中... status={status or 'unknown'} 已等待 {int(elapsed)}s", file=sys.stderr)
            last_status = status
            last_report = elapsed
        time.sleep(TASK_POLL_INTERVAL)


def extract_images_from_data_list(data_list):
    images = []
    if not isinstance(data_list, list):
        return images
    for item in data_list:
        if not isinstance(item, dict):
            continue
        image_url = str(item.get("url") or "").strip()
        if image_url:
            images.append(image_url)
            continue
        if item.get("b64_json"):
            # 兜底：个别模型可能仍返回 b64_json，解码为本地临时文件
            images.append(b64_image_to_tempfile(item["b64_json"]))
    return images


def collect_task_images(task):
    result = task.get("result") if isinstance(task, dict) else None
    if not isinstance(result, dict):
        result = {}

    images = extract_images_from_data_list(result.get("data"))
    top_level_url = str(task.get("image_url") or "").strip() if isinstance(task, dict) else ""
    if top_level_url:
        images.append(top_level_url)

    images = dedupe_images(images)
    usage = result.get("usage")
    created = result.get("created") or task.get("completed_at") or task.get("created_at")
    return images, usage, created


def is_image_url(data):
    """检查数据是否为有效的图片URL"""
    if not data or not isinstance(data, str):
        return False
    if data.startswith(("http://", "https://")):
        try:
            parsed = urllib.parse.urlparse(data)
            return all([parsed.scheme, parsed.netloc])
        except Exception:
            return False
    return False


def download_image_to_tempfile(url):
    """下载远程图片到临时文件，返回临时文件路径"""
    request = urllib.request.Request(
        url,
        headers={"Accept": "*/*", "User-Agent": "image-2-skill/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        content = response.read()
        content_type = response.headers.get("Content-Type", "")

    # 从 URL 或 Content-Type 推断扩展名
    parsed_url = urllib.parse.urlparse(str(url or "").strip())
    url_suffix = Path(urllib.parse.unquote(parsed_url.path)).suffix.lower()
    extension = url_suffix if url_suffix else ""
    if not extension:
        ct = str(content_type or "").split(";", 1)[0].strip().lower()
        ct_map = {
            "image/jpeg": ".jpg", "image/png": ".png",
            "image/webp": ".webp", "image/gif": ".gif",
        }
        extension = ct_map.get(ct, "") or mimetypes.guess_extension(ct) or ".png"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    try:
        temp_file.write(content)
        temp_file.flush()
        return temp_file.name
    finally:
        temp_file.close()


def dedupe_images(images):
    """去重图片 URL"""
    deduped = []
    seen = set()
    for image in images:
        if image in seen:
            continue
        seen.add(image)
        deduped.append(image)
    return deduped


def build_multipart_form(fields, files):
    boundary = f"----codex-image-2-{uuid.uuid4().hex}"
    parts = []

    for field_name, field_value in fields:
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(
            f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n{field_value}\r\n'.encode("utf-8")
        )

    for field_name, file_path in files:
        target_path = Path(file_path).expanduser()
        if not target_path.exists() or not target_path.is_file():
            raise RuntimeError(f"参考图片不存在: {target_path}")

        file_name = target_path.name
        file_mime_type = resolve_file_mime_type(str(target_path))
        file_bytes = target_path.read_bytes()

        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(
            (
                f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'
                f"Content-Type: {file_mime_type}\r\n\r\n"
            ).encode("utf-8")
        )
        parts.append(file_bytes)
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(parts)


def validate_size(size):
    if size not in SUPPORTED_SIZES:
        allowed = ", ".join(
            f"{ratio}={preset}" for ratio, preset in SUPPORTED_SIZE_PRESETS.items()
        )
        raise ValueError(f"不支持的尺寸 '{size}'。当前仅支持以下比例与像素：{allowed}")
    return size


def generate_image(prompt, size="2048x2048", model=DEFAULT_MODEL, agent_id=None):
    if not IMAGE_2_API_BASE_URL:
        return {"error": "缺少 IMAGE_2_API_BASE_URL；请先配置实际服务端点。"}
    if not API_KEY:
        return {"error": "缺少 IMAGE_2_API_KEY 或 OPENAI_API_KEY；请通过环境变量显式配置凭据。"}

    size = validate_size(size)

    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
    }

    try:
        task_id = submit_image_task(IMAGE_GENERATION_ASYNC_URL, payload, agent_id=agent_id)
        task = wait_for_image_task(task_id, agent_id=agent_id)

        images, usage, created = collect_task_images(task)
        if not images:
            return {"error": "Failed to extract image url from completed task"}

        return {
            "success": True,
            "mode": "generation",
            "task_id": task_id,
            "images": images,
            "usage": usage,
            "created": created,
        }
    except Exception as error:
        return {"error": str(error)}


def edit_image(prompt, image_paths, model=DEFAULT_MODEL, size=None, agent_id=None):
    if not IMAGE_2_API_BASE_URL:
        return {"error": "缺少 IMAGE_2_API_BASE_URL；请先配置实际服务端点。"}
    if not API_KEY:
        return {"error": "缺少 IMAGE_2_API_KEY 或 OPENAI_API_KEY；请通过环境变量显式配置凭据。"}
    if not image_paths:
        return {"error": "图生图需要至少一个 --image 参数"}

    try:
        form_fields = [
            ("model", model),
            ("prompt", prompt),
        ]
        if size:
            size = validate_size(size)
            form_fields.append(("size", size))

        boundary, body = build_multipart_form(
            fields=form_fields,
            files=[
                (f"image[{index}]", image_path)
                for index, image_path in enumerate(image_paths)
            ],
        )

        task_id = submit_image_task(
            IMAGE_EDIT_ASYNC_URL,
            body,
            content_type=f"multipart/form-data; boundary={boundary}",
            agent_id=agent_id,
        )
        if task_id == "__sync_response__":
            # 同步响应，直接从 response_json 提取 b64_json
            response_json = request_json(
                IMAGE_EDIT_ASYNC_URL,
                method="POST",
                headers=build_image_auth_headers(content_type=f"multipart/form-data; boundary={boundary}", agent_id=agent_id),
                payload=body,
                timeout=120,
            )
            images, usage, created = collect_task_images(response_json)
            if not images:
                return {"error": "Failed to extract image from sync response"}
            return {
                "success": True,
                "mode": "edit",
                "task_id": "sync",
                "images": images,
                "usage": usage,
                "created": created,
            }
        task = wait_for_image_task(task_id, agent_id=agent_id)

        images, usage, created = collect_task_images(task)
        if not images:
            return {"error": "Failed to extract image url from completed task"}

        return {
            "success": True,
            "mode": "edit",
            "task_id": task_id,
            "images": images,
            "usage": usage,
            "created": created,
        }
    except Exception as error:
        return {"error": str(error)}


# ---- 两阶段确认机制（参考 seedance 交互模式）----

CONFIRMATION_MANIFEST_VERSION = 2
CONFIRMATION_DIR = Path(os.environ.get("CODEX_ARTIFACT_DIR", Path.cwd() / "createContent")) / "image" / ".confirmations"


def sha256_text(value):
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def canonical_json_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def normalize_fingerprint(value):
    normalized = str(value or "").strip().lower()
    if normalized.startswith("sha256:"):
        normalized = normalized.split(":", 1)[1]
    return normalized


def calculate_confirmation_fingerprint(manifest):
    unsigned = {key: value for key, value in manifest.items() if key != "fingerprint"}
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def build_confirmation_manifest(prompt, images, size, model, agent_id=None):
    normalized_prompt = str(prompt or "")
    normalized_images = [str(item or "") for item in (images or [])]
    normalized_agent_id = str(agent_id or "").strip()
    if not normalized_agent_id:
        raise ValueError("准备确认清单时必须提供 agent_id")
    manifest = {
        "version": CONFIRMATION_MANIFEST_VERSION,
        "confirmation_id": f"image2-{uuid.uuid4().hex}",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "request": {
            "agent_id": normalized_agent_id,
            "mode": "edit" if normalized_images else "generation",
            "prompt": normalized_prompt,
            "prompt_sha256": sha256_text(normalized_prompt),
            "images": normalized_images,
            "image_count": len(normalized_images),
            "size": str(size or ""),
            "model": str(model or DEFAULT_MODEL),
        },
    }
    manifest["fingerprint"] = calculate_confirmation_fingerprint(manifest)
    return manifest


def write_confirmation_manifest(manifest, confirmation_output=None):
    if confirmation_output:
        target_path = Path(confirmation_output).expanduser().resolve()
        if target_path.is_dir():
            target_path = target_path / f"{manifest['confirmation_id']}.json"
    else:
        target_dir = CONFIRMATION_DIR.resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{manifest['confirmation_id']}.json"

    target_path = target_path.expanduser().resolve()
    if target_path.exists():
        raise RuntimeError(
            f"确认清单文件已存在，为避免覆盖已确认输入已拒绝写入: {target_path}"
        )
    with open(target_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2, sort_keys=True)
    try:
        target_path.chmod(0o600)
    except OSError:
        pass
    return target_path


def load_confirmation_manifest(confirmation_file):
    path = Path(str(confirmation_file or "")).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"确认清单文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as file:
        manifest = json.load(file)
    if not isinstance(manifest, dict):
        raise RuntimeError("确认清单根对象必须是 JSON object")
    return manifest


def validate_confirmation_manifest(manifest, expected_fingerprint=None):
    if manifest.get("version") != CONFIRMATION_MANIFEST_VERSION:
        raise RuntimeError(f"不支持的确认清单版本: {manifest.get('version')}")
    stored = normalize_fingerprint(manifest.get("fingerprint"))
    calculated = calculate_confirmation_fingerprint(manifest)
    if not stored or not hmac.compare_digest(stored, calculated):
        raise RuntimeError(
            "确认清单指纹校验失败：prompt、参考图或参数在准备后可能被修改。"
            "请重新准备并取得新确认，不要继续生成。"
        )
    expected = normalize_fingerprint(expected_fingerprint)
    if expected and not hmac.compare_digest(expected, stored):
        raise RuntimeError("传入的 --confirm-fingerprint 与清单指纹不一致，拒绝执行。")
    request = manifest.get("request")
    if not isinstance(request, dict) or not str(request.get("agent_id") or "").strip():
        raise RuntimeError("确认清单缺少 agent_id，必须重新准备并取得新确认。")
    return manifest


def prepare_confirmation(prompt, images, size, model, agent_id=None, confirmation_output=None):
    validated_size = validate_size(size)
    manifest = build_confirmation_manifest(
        prompt=prompt,
        images=images,
        size=validated_size,
        model=model,
        agent_id=agent_id,
    )
    target_path = write_confirmation_manifest(manifest, confirmation_output=confirmation_output)
    request = manifest["request"]

    warnings = []
    for index, image in enumerate(request["images"], start=1):
        if not is_image_url(image):
            warnings.append(
                f"参考图 {index} 是本地路径而非完整 URL（{image}），确认表会展示本地路径。"
                "如需展示完整 URL，请在准备阶段直接传入参考图的原始 URL。"
            )

    return {
        "success": True,
        "confirmation_id": manifest["confirmation_id"],
        "confirmation_file": str(target_path),
        "confirmation_fingerprint": manifest["fingerprint"],
        "api_request_sent": False,
        "mode": request["mode"],
        "prompt": request["prompt"],
        "prompt_sha256": request["prompt_sha256"],
        "agent_id": request["agent_id"],
        "images": request["images"],
        "image_count": request["image_count"],
        "size": request["size"],
        "model": request["model"],
        "warnings": warnings,
    }


def run_with_confirmation(confirmation_file, confirm_fingerprint, dry_run=False):
    manifest = load_confirmation_manifest(confirmation_file)
    validate_confirmation_manifest(manifest, expected_fingerprint=confirm_fingerprint)
    request = manifest.get("request") or {}
    mode = request.get("mode") or ("edit" if request.get("images") else "generation")
    prompt = request.get("prompt", "")
    agent_id = str(request.get("agent_id") or "").strip()
    images = list(request.get("images") or [])
    size = request.get("size") or "2048x2048"
    model = request.get("model") or DEFAULT_MODEL

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "api_request_sent": False,
            "confirmation_id": manifest.get("confirmation_id"),
            "confirmation_fingerprint": manifest.get("fingerprint"),
            "agent_id": agent_id,
            "mode": mode,
            "prompt": prompt,
            "prompt_sha256": request.get("prompt_sha256"),
            "images": images,
            "image_count": len(images),
            "size": size,
            "model": model,
        }

    temp_files = []
    local_image_paths = []
    for img in images:
        if is_image_url(img):
            try:
                temp_path = download_image_to_tempfile(img)
                temp_files.append(temp_path)
                local_image_paths.append(temp_path)
            except Exception as e:
                print(f"Warning: failed to download image {str(img)[:80]}...: {e}", file=sys.stderr)
        else:
            local_image_paths.append(img)

    try:
        if mode == "edit":
            if not local_image_paths:
                return {"error": "确认清单为图生图模式但无可用参考图"}
            result = edit_image(prompt, local_image_paths, model=model, size=size, agent_id=agent_id)
        else:
            result = generate_image(prompt, size=size, model=model, agent_id=agent_id)
    finally:
        for temp_path in temp_files:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass

    if isinstance(result, dict) and result.get("success"):
        result["confirmation_id"] = manifest.get("confirmation_id")
        result["confirmation_fingerprint"] = manifest.get("fingerprint")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Image-2 图像生成与编辑（异步任务 + 两阶段用户确认）",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",
        default=None,
        help="图片描述文字或编辑要求；准备阶段必填，正式生成阶段不传",
    )
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        metavar="PATH_OR_URL",
        help="参考图本地路径或 URL，可重复；仅准备阶段使用，按上传顺序保留",
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        default=None,
        help="准备阶段必填的 Agent ID；正式阶段从确认清单读取",
    )
    parser.add_argument(
        "--size",
        type=str,
        default="2048x2048",
        help="尺寸，仅支持 1:1/2:3/3:2/3:4/4:3/4:5/5:4/9:16/16:9/21:9 对应的 2K 预设像素",
    )
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="模型名称")
    parser.add_argument("--json", action="store_true", help="以纯 JSON 格式输出结果")

    parser.add_argument(
        "--prepare-confirmation",
        action="store_true",
        help="离线固化 prompt/参考图/参数并生成确认清单，不请求 API",
    )
    parser.add_argument("--confirmation-file", type=str, default=None, help="使用已确认清单正式生成或 dry-run")
    parser.add_argument("--confirm-fingerprint", type=str, default=None, help="用户确认时展示的完整 SHA-256 指纹")
    parser.add_argument("--confirmation-output", type=str, default=None, help="准备阶段确认清单的输出目录或文件路径")
    parser.add_argument("--confirm", action="store_true", help="正式生成必填，表示用户已确认当前清单")
    parser.add_argument("--dry-run", action="store_true", help="校验确认清单并展示将提交的输入，不请求 API")

    args = parser.parse_args()

    # 模式一：离线准备确认清单（不请求 API）
    if args.prepare_confirmation:
        if not args.prompt:
            print("错误：准备确认清单时必须提供 prompt", file=sys.stderr)
            return
        if not args.agent_id:
            print("错误：准备确认清单时必须提供 --agent-id", file=sys.stderr)
            return
        images = list(args.image)
        images = dedupe_images(images)
        try:
            result = prepare_confirmation(
                prompt=args.prompt,
                images=images,
                size=args.size,
                model=args.model,
                agent_id=args.agent_id,
                confirmation_output=args.confirmation_output,
            )
        except Exception as e:
            result = {"error": str(e)}
        print(json.dumps(result, ensure_ascii=False))
        return

    # 模式二：使用已确认清单正式生成（或 dry-run）
    if args.confirmation_file:
        if args.prompt or args.image or args.agent_id:
            print(
                "错误：使用 --confirmation-file 时禁止再传 prompt、--image 或 --agent-id，已确认输入不可变（尺寸/模型以清单为准）",
                file=sys.stderr,
            )
            return
        if not args.confirm_fingerprint:
            print(
                "错误：使用 --confirmation-file 必须传 --confirm-fingerprint（与确认清单一致的 SHA-256 指纹）",
                file=sys.stderr,
            )
            return
        if args.dry_run:
            if args.confirm:
                print("错误：--dry-run 不得携带 --confirm（dry-run 不正式生成）", file=sys.stderr)
                return
        elif not args.confirm:
            print("错误：正式生成必须传 --confirm 表示用户已确认当前清单", file=sys.stderr)
            return
        result = run_with_confirmation(
            confirmation_file=args.confirmation_file,
            confirm_fingerprint=args.confirm_fingerprint,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            if "success" in result:
                for url in result.get("images", []):
                    print(url)
            else:
                print(f"错误: {result.get('error')}")
        return

    # 未走两阶段确认：拒绝直接生成
    parser.print_help(sys.stderr)
    print(
        "\n错误：必须先 --prepare-confirmation 准备确认清单并取得用户确认，"
        "再用 --confirmation-file 正式生成。禁止直接传 prompt/--image 生成。",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
