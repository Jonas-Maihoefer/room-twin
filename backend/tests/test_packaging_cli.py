from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

import pytest
from pxr import Sdf, Usd, UsdGeom, UsdUtils

from app.usd import AssetCatalog, PackagingError, package_usdz, process_roomplan, validate_usdz
from app.usd.cli import main


BACKEND = Path(__file__).parents[1]
SOURCE = BACKEND / "testdata" / "room.usdz"
SCAN = BACKEND / "testdata" / "room.json"
METADATA = BACKEND / "testdata" / "metadata.json"


def _mesh_fingerprints(stage, prefix):
    found = {}
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh) and prim.GetPath().HasPrefix(prefix):
            mesh = UsdGeom.Mesh(prim)
            found[str(prim.GetPath())] = (
                tuple(tuple(float(v) for v in p) for p in mesh.GetPointsAttr().Get() or ()),
                tuple(mesh.GetFaceVertexCountsAttr().Get() or ()),
                tuple(mesh.GetFaceVertexIndicesAttr().Get() or ()),
            )
    return found


def _world_transforms(stage, prefix):
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    return {str(prim.GetPath()): tuple(float(cache.GetLocalToWorldTransform(prim)[r][c])
                                        for r in range(4) for c in range(4))
            for prim in stage.Traverse() if prim.GetPath().HasPrefix(prefix)}


def test_real_scan_cli_usdz_is_self_contained_and_preserves_architecture(tmp_path):
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    original = Usd.Stage.Open(str(SOURCE))
    assert original and original.GetDefaultPrim()
    architecture_before = _mesh_fingerprints(original, "/room/Mesh_grp/Arch_grp")
    architecture_xforms_before = _world_transforms(original, "/room/Mesh_grp/Arch_grp")
    assert architecture_before

    output = tmp_path / "enhanced.usdz"
    command = [sys.executable, "-m", "app.usd.cli", "replace", "--usdz", str(SOURCE),
               "--json", str(SCAN), "--metadata", str(METADATA), "--output", str(output)]
    cli_env = os.environ.copy()
    for name in ("TMP", "TEMP", "TMPDIR"):
        cli_env[name] = str(tmp_path)
    cli_result = subprocess.run(command, cwd=BACKEND, env=cli_env, text=True, capture_output=True)
    assert cli_result.returncode == 0, cli_result.stderr
    assert not list(tmp_path.glob("room-twin-work-*"))
    report_path = tmp_path / "enhanced.report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "room-twin.replacement-report.v1"
    assert report["catalog_version"] == 1
    assert (report["furniture_detected"], report["furniture_replaced"], report["furniture_preserved"]) == (8, 6, 2)
    assert sum(obj["status"] == "replaced" for obj in report["objects"]) == 6
    assert sum(obj["status"] != "replaced" for obj in report["objects"]) == 2
    assert Counter(obj["category"] for obj in report["objects"]) == {
        "chair": 3, "table": 2, "storage": 2, "bed": 1,
    }
    assert Counter(obj["category"] for obj in report["objects"] if obj["status"] == "replaced") == {
        "chair": 3, "table": 2, "storage": 1,
    }
    assert {obj["category"] for obj in report["objects"] if obj["status"] != "replaced"} == {"storage", "bed"}
    assert report["validation"]["status"] == "passed"
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash

    packaged = Usd.Stage.Open(str(output))
    assert packaged and packaged.GetDefaultPrim()
    assert _mesh_fingerprints(packaged, "/room/Mesh_grp/Arch_grp") == architecture_before
    assert _world_transforms(packaged, "/room/Mesh_grp/Arch_grp") == architecture_xforms_before
    resolved = UsdUtils.ComputeAllDependencies(Sdf.AssetPath(packaged.GetRootLayer().identifier))
    assert not resolved[-1], resolved[-1]

    replaced = [obj for obj in report["objects"] if obj["status"] == "replaced"]
    preserved = [obj for obj in report["objects"] if obj["status"] != "replaced"]
    for entry in replaced:
        source_prim = packaged.GetPrimAtPath(entry["prim_path"])
        replacement_path = source_prim.GetParent().GetPath().AppendChild(
            f"RoomTwinReplacement_{entry['uuid'].replace('-', '')}")
        replacement = packaged.GetPrimAtPath(replacement_path)
        meshes = [p for p in Usd.PrimRange(replacement) if p.IsA(UsdGeom.Mesh)]
        assert meshes and all(UsdGeom.Mesh(mesh).GetPointsAttr().Get() for mesh in meshes)
        assert all(UsdGeom.Imageable(mesh).ComputeVisibility() != UsdGeom.Tokens.invisible for mesh in meshes)
        assert entry["model"] and entry["model"].startswith("models/")
        source_pose = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(source_prim)
        replacement_pose = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(replacement)
        assert tuple(float(source_pose[r][c]) for r in range(4) for c in range(4)) == pytest.approx(
            tuple(float(replacement_pose[r][c]) for r in range(4) for c in range(4)), abs=0.002)
    for entry in preserved:
        source_prim = packaged.GetPrimAtPath(entry["prim_path"])
        assert any(p.IsA(UsdGeom.Mesh) and UsdGeom.Imageable(p).ComputeVisibility() != UsdGeom.Tokens.invisible
                   for p in Usd.PrimRange(source_prim))

    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert names and names[0].lower().endswith((".usd", ".usda", ".usdc"))
        normalized_names = [name.replace("\\", "/") for name in names]
        selected_files = {Path(entry["model"]).name for entry in replaced}
        assert selected_files
        assert all(any(name.endswith(filename) for name in normalized_names) for filename in selected_files)

    # The CLI removes its temporary workspace. Opening from a clean directory
    # exercises a fresh process with no access to the backend asset catalog.
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    script = (
        "from pxr import Sdf, Usd, UsdGeom, UsdUtils; import os, sys; "
        "s=Usd.Stage.Open(sys.argv[1]); assert s and s.GetDefaultPrim(); "
        "m=[p for p in s.Traverse() if p.IsA(UsdGeom.Mesh)]; assert len(m)>0; "
        "d=UsdUtils.ComputeAllDependencies(Sdf.AssetPath(s.GetRootLayer().identifier)); assert not d[-1], d[-1]; "
        "assert not [l.identifier for l in s.GetUsedLayers() if os.path.isabs(l.identifier) "
        "and os.path.normcase(l.identifier) != os.path.normcase(sys.argv[1]) "
        "and '[' not in l.identifier], "
        "[l.identifier for l in s.GetUsedLayers() if os.path.isabs(l.identifier) "
        "and os.path.normcase(l.identifier) != os.path.normcase(sys.argv[1]) and '[' not in l.identifier]; "
        "assert not [a for a in d[1] if os.path.isabs(a) and os.path.normcase(a) != os.path.normcase(sys.argv[1]) "
        "and not os.path.normcase(a).startswith(os.path.normcase(sys.argv[1])+'[')], d[1]; "
        "assert any('RoomTwinReplacement_' in str(p.GetPath()) for p in s.Traverse())"
    )
    completed = subprocess.run([sys.executable, "-c", script, str(output)], cwd=isolated,
                               env={k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PXR_PLUGINPATH_NAME"}},
                               text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr


def test_packager_rejects_invalid_or_existing_output(tmp_path):
    catalog = AssetCatalog.load()
    result = process_roomplan(SOURCE, SCAN, catalog, tmp_path / "workspace")
    existing = tmp_path / "existing.usdz"
    existing.write_bytes(b"keep me")
    with pytest.raises(PackagingError, match="already exists"):
        package_usdz(result, existing)
    assert existing.read_bytes() == b"keep me"
    with pytest.raises(PackagingError, match="end in .usdz"):
        package_usdz(result, tmp_path / "wrong.zip")
    bad = tmp_path / "invalid.usdz"
    bad.write_bytes(b"not a USDZ")
    validation = validate_usdz(bad)
    assert not validation.valid and validation.errors


def test_missing_replacement_dependency_fails_without_partial_output(tmp_path):
    result = process_roomplan(SOURCE, SCAN, AssetCatalog.load(), tmp_path / "workspace")
    result.dependencies[0].unlink()
    output = tmp_path / "missing-dependency.usdz"
    with pytest.raises(PackagingError):
        package_usdz(result, output)
    assert not output.exists()


def test_cli_missing_inputs_returns_nonzero_without_output(tmp_path, capsys):
    output = tmp_path / "missing.usdz"
    status = main(["replace", "--usdz", str(tmp_path / "missing.usdz"),
                   "--json", str(SCAN), "--output", str(output)])
    assert status != 0
    assert "does not exist" in capsys.readouterr().err
    assert not output.exists()


def test_cli_malformed_json_returns_nonzero_without_output(tmp_path, capsys):
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{bad json", encoding="utf-8")
    output = tmp_path / "malformed-output.usdz"
    status = main(["replace", "--usdz", str(SOURCE), "--json", str(malformed),
                   "--output", str(output)])
    assert status != 0
    assert "cannot load RoomPlan scan" in capsys.readouterr().err
    assert not output.exists()
