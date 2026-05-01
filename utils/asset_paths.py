import hashlib
import os
import re
import shutil
import sys


def _storage_root_dir():
    configured = (os.getenv("RESUMECABINET_DATA_ROOT") or "").strip()
    if configured:
        return configured
    return os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "ResumeCabinet")


def external_assets_dir():
    return os.path.join(_storage_root_dir(), "assets")


def runtime_base_dir():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def normalize_asset_reference(path_value):
    if not path_value:
        return path_value

    path_value = path_value.strip().replace("\\", "/")

    # Bundled or materialized user assets (stable after first save)
    if path_value.startswith("images/") or path_value.startswith("user/"):
        return path_value

    # Convert absolute legacy paths ending in images/logo|profile/...
    match = re.search(r"images/(logo|profile)/(.+)$", path_value, re.IGNORECASE)
    if match:
        return f"images/{match.group(1).lower()}/{match.group(2)}"

    # Convert absolute paths inside external assets override
    ext_assets = external_assets_dir().replace("\\", "/")
    if path_value.lower().startswith(ext_assets.lower() + "/"):
        rel = path_value[len(ext_assets) + 1 :]
        return rel

    return path_value


def _is_under_dir(path, root):
    try:
        p = os.path.normcase(os.path.normpath(path))
        r = os.path.normcase(os.path.normpath(root))
        return os.path.commonpath([p, r]) == r
    except (ValueError, OSError):
        return False


def _safe_user_asset_filename(src_abs: str) -> str:
    base = os.path.basename(src_abs)
    stem, ext = os.path.splitext(base)
    ext_l = (ext or "").lower()
    if ext_l not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".tif", ".tiff"):
        ext = ".png"
    stem_clean = re.sub(r"[^a-zA-Z0-9._-]+", "_", stem).strip("._") or "img"
    stem_clean = stem_clean[:50]
    digest = hashlib.sha256(
        os.path.normcase(os.path.normpath(src_abs)).encode("utf-8", errors="replace")
    ).hexdigest()[:12]
    return f"{stem_clean}__{digest}{ext}"


def _ingest_file_into_user_assets(src_abs: str) -> str:
    ext_root = external_assets_dir()
    user_root = os.path.join(ext_root, "user")
    os.makedirs(user_root, exist_ok=True)
    name = _safe_user_asset_filename(src_abs)
    dest = os.path.join(user_root, name)
    shutil.copy2(src_abs, dest)
    return f"user/{name.replace(os.sep, '/')}"


def materialize_user_media_path(path_value: str) -> str:
    """
    Copy disk files selected by the user into <storage_root>/assets/user/
    and return a stable relative reference (user/...).

    Bundled templates use images/... inside the PyInstaller bundle; user picks should
    not depend on cwd or exe location, so previews and PDFs keep working after compile.
    """
    if path_value is None or not str(path_value).strip():
        return path_value
    raw = str(path_value).strip()
    n = normalize_asset_reference(raw)
    if not n:
        return n

    ext_root = external_assets_dir()

    if n.startswith("images/"):
        return n

    if n.startswith("user/"):
        full = os.path.join(ext_root, n.replace("/", os.sep))
        return n.replace("\\", "/")

    fs_path = os.path.normpath(n.replace("/", os.sep))
    if os.path.isfile(fs_path) and os.path.isabs(fs_path):
        if _is_under_dir(fs_path, ext_root):
            try:
                rel = os.path.relpath(fs_path, ext_root).replace("\\", "/")
                return rel
            except ValueError:
                pass
        return _ingest_file_into_user_assets(fs_path)

    return n.replace("\\", "/")


def resolve_asset_path(path_value):
    if not path_value:
        return path_value

    normalized = normalize_asset_reference(path_value)

    if os.path.isabs(normalized.replace("/", os.sep)):
        ap = os.path.normpath(normalized.replace("/", os.sep))
        return ap

    candidates = [
        os.path.join(external_assets_dir(), normalized),
        os.path.join(runtime_base_dir(), normalized),
        os.path.abspath(os.path.normpath(normalized.replace("/", os.sep))),
    ]
    for candidate in candidates:
        cand = os.path.normpath(candidate)
        if os.path.isfile(cand):
            return cand
    return normalized
