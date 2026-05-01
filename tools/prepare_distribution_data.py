#!/usr/bin/env python3
"""
Ejecutar tras PyInstaller para crear dist/data con global/software, global/languages,
defaults/avatars, defaults/example_templates (plantillas borrables al copiarlas al perfil),
y el resto para el ZIP portable junto al .exe en dist/.

Uso: python tools/prepare_distribution_data.py
"""

import pathlib
import sys

# Permite import utils.* desde la raíz del proyecto
_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main():
    from utils.portable_media_bootstrap import (
        bootstrap_portable_asset_tree,
        seed_defaults_example_templates_into_storage,
    )

    data_root = _ROOT / "dist" / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    images = _ROOT / "images"
    bootstrap_portable_asset_tree(str(data_root), str(images))
    seed_defaults_example_templates_into_storage(str(data_root), str(_ROOT))
    print(f"Portable data tree: {data_root}")


if __name__ == "__main__":
    main()
