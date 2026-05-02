"""Tests for idempotent bootstrap of defaults and user template folders."""

from pathlib import Path

from utils.portable_media_bootstrap import (
    LANGUAGE_LOGO_STEMS,
    seed_defaults_example_templates_into_storage,
    seed_user_templates_folder_if_empty,
)


def test_language_logo_stems_contains_expected_python_variants():
    assert "python_logo" in LANGUAGE_LOGO_STEMS
    assert "csharp_logo" in LANGUAGE_LOGO_STEMS


def test_seed_defaults_example_templates_idempotent(tmp_path):
    repo = tmp_path / "repo"
    (repo / "defaults" / "example_templates").mkdir(parents=True)
    (repo / "defaults" / "example_templates" / "A.json").write_text("{}", encoding="utf-8")

    storage = tmp_path / "data"
    storage.mkdir()

    seed_defaults_example_templates_into_storage(str(storage), str(repo))
    first = Path(storage / "defaults" / "example_templates" / "A.json")
    assert first.is_file()

    stamp = first.read_bytes()
    (repo / "defaults" / "example_templates" / "A.json").write_text('{"changed":true}', encoding="utf-8")

    seed_defaults_example_templates_into_storage(str(storage), str(repo))
    assert first.read_bytes() == stamp


def test_seed_user_templates_only_when_folder_has_no_json(tmp_path):
    storage = tmp_path / "storage"
    ex = storage / "defaults" / "example_templates"
    ex.mkdir(parents=True)
    (ex / "Demo.json").write_text("{}", encoding="utf-8")

    ud = tmp_path / "users" / "u1" / "templates"
    ud.mkdir(parents=True)
    seed_user_templates_folder_if_empty(str(ud), str(ex))
    assert (ud / "Demo.json").is_file()

    ud2 = tmp_path / "users" / "u2" / "templates"
    ud2.mkdir(parents=True)
    (ud2 / "Custom.json").write_text("{}", encoding="utf-8")
    seed_user_templates_folder_if_empty(str(ud2), str(ex))
    assert not (ud2 / "Demo.json").exists()

