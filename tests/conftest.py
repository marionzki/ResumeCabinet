import pytest


@pytest.fixture
def tmp_data_root(tmp_path, monkeypatch):
    """
    Isolate portable tree under pytest tmp_path without touching real APPDATA.
    Paths in utils/asset_paths.py read RESUMECABINET_DATA_ROOT on each call.
    """
    root = tmp_path / "resume_data"
    root.mkdir(parents=True)
    monkeypatch.setenv("RESUMECABINET_DATA_ROOT", str(root))
    return root
