"""
Copia inicial de PNG empaquetados (images/logo, images/profile) y plantillas de ejemplo
(defaults/example_templates → data/defaults/example_templates → templates del usuario cuando está vacío).
"""
import os
import shutil


# Stems (sin extensión, minúsculas) que pertenecen a lenguajes, no software.
LANGUAGE_LOGO_STEMS = frozenset(
    {
        "python_logo",
        "vba_logo",
        "csharp_logo",
        "cplus_logo",
        "sql_logo",
    }
)


def _copy_png_missing_only(src_dir: str, dst_dir: str) -> int:
    if not os.path.isdir(src_dir):
        return 0
    os.makedirs(dst_dir, exist_ok=True)
    copied = 0
    for name in os.listdir(src_dir):
        if not name.lower().endswith(".png"):
            continue
        s = os.path.join(src_dir, name)
        if not os.path.isfile(s):
            continue
        d = os.path.join(dst_dir, name)
        if not os.path.isfile(d):
            shutil.copy2(s, d)
            copied += 1
    return copied


def bootstrap_portable_asset_tree(storage_root: str, bundle_images_root: str) -> None:
    """
    Crea data/global/software, data/global/languages y data/defaults/avatars,
    copiando desde bundle_images_root/logo y bundle_images_root/profile.
    No sobrescribe PNG ya presentes en destino (idempotente).
    """
    g_soft = os.path.join(storage_root, "global", "software")
    g_lang = os.path.join(storage_root, "global", "languages")
    def_av = os.path.join(storage_root, "defaults", "avatars")
    os.makedirs(g_soft, exist_ok=True)
    os.makedirs(g_lang, exist_ok=True)
    os.makedirs(def_av, exist_ok=True)

    logo_dir = os.path.join(bundle_images_root, "logo")
    if os.path.isdir(logo_dir):
        for name in os.listdir(logo_dir):
            if not name.lower().endswith(".png"):
                continue
            src = os.path.join(logo_dir, name)
            if not os.path.isfile(src):
                continue
            stem = os.path.splitext(name)[0].lower()
            dst_dir = g_lang if stem in LANGUAGE_LOGO_STEMS else g_soft
            dst = os.path.join(dst_dir, name)
            if not os.path.isfile(dst):
                shutil.copy2(src, dst)

    prof = os.path.join(bundle_images_root, "profile")
    if os.path.isdir(prof):
        _copy_png_missing_only(prof, def_av)


def seed_defaults_example_templates_into_storage(storage_root: str, repo_root: str | None = None) -> None:
    """
    Rellena <storage>/defaults/example_templates con JSON de ejemplo (no sobrescribe si ya existe).
    repo_root: raíz del proyecto al desarrollar; en exe portable omitir y usar sólo datos ya en data/
    """
    dst = os.path.join(storage_root, "defaults", "example_templates")
    os.makedirs(dst, exist_ok=True)
    if not repo_root:
        return
    src = os.path.join(repo_root, "defaults", "example_templates")
    if not os.path.isdir(src):
        return
    for name in os.listdir(src):
        if not name.endswith(".json"):
            continue
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isfile(s) and not os.path.isfile(d):
            shutil.copy2(s, d)


def seed_user_templates_folder_if_empty(user_templates_dir: str, defaults_example_dir: str) -> None:
    """
    Si templates/ del usuario no tiene ningún .json, copia los ejemplos desde defaults/example_templates.
    Tras borrar todo manualmente la carpeta queda sin volver a poblar hasta nuevos cambios conscientes (perfil nuevo / migración).
    """
    if not os.path.isdir(defaults_example_dir):
        return
    os.makedirs(user_templates_dir, exist_ok=True)
    has_json = False
    for f in os.listdir(user_templates_dir):
        if f.endswith(".json") and os.path.isfile(os.path.join(user_templates_dir, f)):
            has_json = True
            break
    if has_json:
        return
    for name in os.listdir(defaults_example_dir):
        if not name.endswith(".json"):
            continue
        s = os.path.join(defaults_example_dir, name)
        d = os.path.join(user_templates_dir, name)
        if os.path.isfile(s) and not os.path.isfile(d):
            shutil.copy2(s, d)


def seed_user_avatars_from_defaults(storage_root: str, user_key: str) -> None:
    """Si el perfil no tiene avatares, copia los de defaults/avatars."""
    if not user_key:
        return
    src = os.path.join(storage_root, "defaults", "avatars")
    dst = os.path.join(storage_root, "users", user_key, "avatar")
    if not os.path.isdir(src):
        return
    os.makedirs(dst, exist_ok=True)
    has_any = any(
        f.lower().endswith(".png") for f in os.listdir(dst) if os.path.isfile(os.path.join(dst, f))
    )
    if has_any:
        return
    _copy_png_missing_only(src, dst)
