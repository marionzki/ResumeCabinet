"""
Portable asset path helpers used by CV editors and PDF rendering.

Stable relative prefixes (under RESUMECABINET_DATA_ROOT / storage root):
    global/software/, global/languages/, users/<key>/avatar/
Legacy transports still accepted: images/..., user/..., and absolute picks under legacy assets/*.
Resolution order is implemented in resolve_asset_path().
"""

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


def global_software_media_dir():
    return os.path.join(_storage_root_dir(), "global", "software")


def global_languages_media_dir():
    return os.path.join(_storage_root_dir(), "global", "languages")


def user_avatar_media_dir(user_key: str):
    return os.path.join(_storage_root_dir(), "users", user_key or "", "avatar")


def ensure_category_media_dirs(user_key: str | None = None):
    os.makedirs(global_software_media_dir(), exist_ok=True)
    os.makedirs(global_languages_media_dir(), exist_ok=True)
    root = external_assets_dir()
    os.makedirs(root, exist_ok=True)
    os.makedirs(os.path.join(root, "user"), exist_ok=True)
    if user_key:
        os.makedirs(user_avatar_media_dir(user_key), exist_ok=True)


_USER_AVATAR_PREFIX_RE = re.compile(r"^users/[^/]+/avatar/", re.I)


def is_storage_managed_media_ref(path_posix: str) -> bool:
    if not path_posix:
        return False
    return (
        path_posix.startswith("global/software/")
        or path_posix.startswith("global/languages/")
        or bool(_USER_AVATAR_PREFIX_RE.match(path_posix))
    )


def normalize_asset_reference(path_value):
    if not path_value:
        return path_value

    stripped = path_value.strip()
    posix = stripped.replace("\\", "/")

    if posix.startswith("images/") or posix.startswith("user/"):
        return posix

    if posix.startswith("global/software/") or posix.startswith("global/languages/"):
        return posix

    if _USER_AVATAR_PREFIX_RE.match(posix):
        return posix

    sr_norm = os.path.normpath(_storage_root_dir())
    fs_abs = os.path.normpath(os.path.abspath(stripped.replace("/", os.sep)))
    if os.path.isfile(fs_abs) and _is_under_dir(fs_abs, sr_norm):
        try:
            return os.path.relpath(fs_abs, sr_norm).replace("\\", "/")
        except ValueError:
            pass

    match = re.search(r"images/(logo|profile)/(.+)$", posix, re.IGNORECASE)
    if match:
        return f"images/{match.group(1).lower()}/{match.group(2)}"

    ext_assets = external_assets_dir().replace("\\", "/")
    if posix.lower().startswith(ext_assets.lower() + "/"):
        return posix[len(ext_assets) + 1 :].lstrip("/")

    return posix


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


def _ingest_into_folder_return_storage_rel(src_abs: str, dest_folder_abs: str) -> str:
    os.makedirs(dest_folder_abs, exist_ok=True)
    name = _safe_user_asset_filename(src_abs)
    dest = os.path.join(dest_folder_abs, name)
    shutil.copy2(src_abs, dest)
    sr = os.path.normpath(_storage_root_dir())
    dest_n = os.path.normpath(dest)
    try:
        return os.path.relpath(dest_n, sr).replace("\\", "/")
    except ValueError:
        return dest_n.replace("\\", "/")


def _ingest_legacy_user_assets(src_abs: str) -> str:
    ext_root = external_assets_dir()
    user_root = os.path.join(ext_root, "user")
    os.makedirs(user_root, exist_ok=True)
    name = _safe_user_asset_filename(src_abs)
    dest = os.path.join(user_root, name)
    shutil.copy2(src_abs, dest)
    rel_assets = os.path.relpath(dest, ext_root).replace("\\", "/")
    return rel_assets


def materialize_media_path(path_value: str, ingest=None, user_key=None) -> str:
    """
    Convierte rutas absolutas externas en referencias bajo RESUMECABINET_DATA_ROOT.
    ingest: "software" | "language" | "avatar" | None (fallback legacy assets/user/)
    """
    if path_value is None or not str(path_value).strip():
        return path_value
    raw = str(path_value).strip()
    n = normalize_asset_reference(raw)
    if not n:
        return n

    if n.startswith("images/"):
        return n.replace("\\", "/")

    sr = os.path.normpath(_storage_root_dir())
    ext_root_abs = os.path.normpath(external_assets_dir())

    if is_storage_managed_media_ref(n):
        cand = os.path.join(sr, n.replace("/", os.sep))
        if os.path.isfile(cand):
            return n.replace("\\", "/")
        full_assets = os.path.join(ext_root_abs, n.replace("/", os.sep))
        if os.path.isfile(full_assets):
            return n.replace("\\", "/")

    if n.startswith("user/"):
        full = os.path.join(ext_root_abs, n.replace("/", os.sep))
        if os.path.isfile(full):
            return n.replace("\\", "/")

    abs_src = os.path.normpath(raw.replace("/", os.sep))
    if os.path.isfile(abs_src) and os.path.isabs(abs_src):
        if _is_under_dir(abs_src, ext_root_abs):
            try:
                return os.path.relpath(abs_src, ext_root_abs).replace("\\", "/")
            except ValueError:
                pass
        if _is_under_dir(abs_src, sr):
            try:
                return os.path.relpath(abs_src, sr).replace("\\", "/")
            except ValueError:
                pass

        if ingest == "software":
            return _ingest_into_folder_return_storage_rel(abs_src, global_software_media_dir())
        if ingest == "language":
            return _ingest_into_folder_return_storage_rel(abs_src, global_languages_media_dir())
        if ingest == "avatar" and user_key:
            return _ingest_into_folder_return_storage_rel(abs_src, user_avatar_media_dir(user_key))

        return _ingest_legacy_user_assets(abs_src)

    rel_fs = os.path.normpath(n.replace("/", os.sep))
    if os.path.isfile(rel_fs) and os.path.isabs(rel_fs):
        if _is_under_dir(rel_fs, sr):
            try:
                return os.path.relpath(rel_fs, sr).replace("\\", "/")
            except ValueError:
                pass

    return n.replace("\\", "/")


def materialize_user_media_path(path_value: str) -> str:
    """Retrocompatibilidad: copia arbitraria en assets/user cuando no hay contexto."""
    return materialize_media_path(path_value, ingest=None, user_key=None)


def resolve_asset_path(path_value):
    if not path_value:
        return path_value

    normalized = normalize_asset_reference(path_value)

    if os.path.isabs(normalized.replace("/", os.sep)):
        ap = os.path.normpath(normalized.replace("/", os.sep))
        return ap if os.path.isfile(ap) else normalized

    sr = os.path.normpath(_storage_root_dir())
    replacements = normalized.replace("/", os.sep)
    candidates = [
        os.path.join(sr, replacements),
        os.path.join(external_assets_dir(), replacements),
        os.path.join(runtime_base_dir(), replacements),
        os.path.abspath(os.path.normpath(replacements)),
    ]
    for candidate in candidates:
        cand = os.path.normpath(candidate)
        if os.path.isfile(cand):
            return cand
    return normalized
