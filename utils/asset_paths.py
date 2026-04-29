import os
import re
import sys


def _appdata_dir():
    return os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "ResumeCabinet")


def external_assets_dir():
    return os.path.join(_appdata_dir(), "assets")


def runtime_base_dir():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def normalize_asset_reference(path_value):
    if not path_value:
        return path_value

    path_value = path_value.strip().replace("\\", "/")

    # Already relative to app assets
    if path_value.startswith("images/"):
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


def resolve_asset_path(path_value):
    if not path_value:
        return path_value

    normalized = normalize_asset_reference(path_value)

    if os.path.isabs(normalized):
        return normalized

    candidates = [
        os.path.join(external_assets_dir(), normalized),
        os.path.join(runtime_base_dir(), normalized),
        os.path.abspath(normalized),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return normalized
