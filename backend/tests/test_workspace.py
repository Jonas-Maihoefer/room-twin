import zipfile

import pytest

from app.usd import WorkspaceError, extract_usdz
from app.usd import workspace


@pytest.mark.parametrize("entry", ["../escape.usda", "C:/drive.usda", "/absolute.usda", "a/../../escape.usda"])
def test_workspace_rejects_traversal_and_absolute_entries(tmp_path, entry):
    source = tmp_path / "bad.usdz"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(entry, "not USD")
    with pytest.raises(WorkspaceError, match="unsafe"):
        extract_usdz(source, tmp_path / "out")


def test_workspace_rejects_case_colliding_paths(tmp_path):
    source = tmp_path / "collision.usdz"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("room.usda", "#usda 1.0")
        archive.writestr("ROOM.USDA", "#usda 1.0")
    with pytest.raises(WorkspaceError, match="colliding"):
        extract_usdz(source, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def _archive(path, entries):
    with zipfile.ZipFile(path, "w") as archive:
        for entry in entries:
            archive.writestr(entry, "#usda 1.0" if entry.endswith(".usda") else "")


def test_workspace_entry_count_limit_boundary_and_cleanup(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "MAX_ARCHIVE_ENTRIES", 3)
    allowed = tmp_path / "allowed.usdz"
    _archive(allowed, ["room.usda", "a/", "b/"])
    assert extract_usdz(allowed, tmp_path / "allowed-out").is_file()

    rejected = tmp_path / "rejected.usdz"
    _archive(rejected, ["room.usda", "a/", "b/", "c/"])
    with pytest.raises(WorkspaceError, match="entry count.*3"):
        extract_usdz(rejected, tmp_path / "rejected-out")
    assert not (tmp_path / "rejected-out").exists()


def test_workspace_nesting_depth_boundary_files_and_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace, "MAX_DIRECTORY_DEPTH", 2)
    allowed = tmp_path / "allowed-depth.usdz"
    _archive(allowed, ["room.usda", "one/two/", "one/two/asset.usda"])
    extract_usdz(allowed, tmp_path / "depth-out")

    deep_dirs = tmp_path / "deep-dirs.usdz"
    _archive(deep_dirs, ["room.usda", "one/two/three/"])
    with pytest.raises(WorkspaceError, match="nesting depth.*2"):
        extract_usdz(deep_dirs, tmp_path / "deep-out")
    assert not (tmp_path / "deep-out").exists()

    deep_file = tmp_path / "deep-file.usdz"
    _archive(deep_file, ["room.usda", "one/two/three/asset.usda"])
    with pytest.raises(WorkspaceError, match="nesting depth.*2"):
        extract_usdz(deep_file, tmp_path / "deep-file-out")
    assert not (tmp_path / "deep-file-out").exists()
