"""Tests for path normalization and resolution (SPEC: portable media prefixes)."""

import os

import pytest

from utils import asset_paths as ap


def test_is_storage_managed_media_ref_detects_known_prefixes():
    assert ap.is_storage_managed_media_ref("global/software/foo.png") is True
    assert ap.is_storage_managed_media_ref("global/languages/bar.png") is True
    assert ap.is_storage_managed_media_ref("users/john_doe/avatar/portrait.png") is True
    assert ap.is_storage_managed_media_ref("images/logo/x.png") is False
    assert ap.is_storage_managed_media_ref("") is False


def test_normalize_passes_through_global_and_avatar_refs(tmp_data_root):
    assert ap.normalize_asset_reference("global/software/X.png") == "global/software/X.png"
    assert ap.normalize_asset_reference("global/languages/Y.png") == "global/languages/Y.png"
    assert ap.normalize_asset_reference("users/u/avatar/z.png") == "users/u/avatar/z.png"


def test_normalize_passes_through_images_and_legacy_user_prefix(tmp_data_root):
    assert ap.normalize_asset_reference("images/logo/a.png") == "images/logo/a.png"
    assert ap.normalize_asset_reference("user/abc123.png") == "user/abc123.png"


def test_normalize_absolute_file_under_storage_becomes_relative(tmp_data_root):
    sub = tmp_data_root / "global" / "software"
    sub.mkdir(parents=True)
    f = sub / "icon.png"
    f.write_bytes(b"x")
    abs_path = str(f.resolve())
    out = ap.normalize_asset_reference(abs_path)
    assert out == "global/software/icon.png"


def test_resolve_asset_path_finds_file_under_storage_root(tmp_data_root):
    dst = tmp_data_root / "global" / "software"
    dst.mkdir(parents=True)
    fpath = dst / "logo.png"
    fpath.write_bytes(b"p")
    resolved = ap.resolve_asset_path("global/software/logo.png")
    assert resolved == os.path.normpath(str(fpath.resolve()))
