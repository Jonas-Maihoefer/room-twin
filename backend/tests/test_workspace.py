import zipfile

import pytest

from app.usd import WorkspaceError, extract_usdz


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
