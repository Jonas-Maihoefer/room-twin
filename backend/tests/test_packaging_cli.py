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
from app.usd import publication


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
    assert report["catalog_version"] == 2
    assert (report["furniture_detected"], report["furniture_replaced"], report["furniture_preserved"]) == (8, 8, 0)
    assert sum(obj["status"] == "replaced" for obj in report["objects"]) == 8
    assert sum(obj["status"] != "replaced" for obj in report["objects"]) == 0
    assert Counter(obj["category"] for obj in report["objects"]) == {
        "chair": 3, "table": 2, "storage": 2, "bed": 1,
    }
    assert Counter(obj["category"] for obj in report["objects"] if obj["status"] == "replaced") == {
        "chair": 3, "table": 2, "storage": 2, "bed": 1,
    }
    assert {obj["category"] for obj in report["objects"] if obj["status"] != "replaced"} == set()
    assert report["validation"]["status"] == "passed"
    assert report["validation"]["geometry"]["status"] == "passed"
    assert report["validation"]["geometry"]["architecture_preserved"]["status"] == "passed"
    assert report["validation"]["geometry"]["object_count_preserved"] == {
        "status": "passed", "expected": 8, "actual": 8,
    }
    assert report["validation"]["geometry"]["replacement_geometry_valid"]["status"] == "passed"
    assert report["validation"]["geometry"]["transforms"]["replacement_world_bounds"]
    assert report["package"]["status"] == "passed"
    assert report["package"]["file_count"] == len(report["package"]["files"])
    assert report["package"]["usd_layers"]
    assert report["package"]["replacement_assets"]
    assert report["package"]["unresolved_dependencies"] == []
    assert report["package"]["external_dependencies_detected"] is False
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
        assert set(report["package"]["files"]) == set(normalized_names)
        assert all(any(member.endswith(Path(asset).name) for member in normalized_names)
                   for asset in report["package"]["replacement_assets"])
    assert all(entry["status"] == "replaced" and entry["reason"] is None
               for entry in report["objects"] if entry["match_type"] == "exact")
    assert all(entry["status"] == "replaced" and entry["reason"] == "category_fallback"
               for entry in report["objects"] if entry["match_type"] == "category_fallback")
    assert all(entry["status"] == "preserved_no_model" and entry["reason"] in
               {"no_matching_catalog_entry", "no_compatible_attribute_match"}
               for entry in report["objects"] if entry["status"] != "replaced")
    assert all(entry["match_type"] in {"exact", "category_fallback", "none"}
               for entry in report["objects"])

    # The CLI removes its temporary workspace. Opening from a clean directory
    # exercises a fresh process with no access to the backend asset catalog.
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    script = f'''\
from pxr import Gf, Sdf, Usd, UsdGeom, UsdUtils
import os, sys
s = Usd.Stage.Open(sys.argv[1])
assert s and s.GetDefaultPrim()
assert any(p.IsA(UsdGeom.Mesh) for p in s.Traverse())
d = UsdUtils.ComputeAllDependencies(Sdf.AssetPath(s.GetRootLayer().identifier))
assert not d[-1], d[-1]
assert any("RoomTwinReplacement_" in str(p.GetPath()) for p in s.Traverse())
assert not [l.identifier for l in s.GetUsedLayers() if os.path.isabs(l.identifier)
            and os.path.normcase(l.identifier) != os.path.normcase(sys.argv[1]) and "[" not in l.identifier]
cache = UsdGeom.XformCache(Usd.TimeCode.Default())
entries = {[(e['uuid'], e['prim_path']) for e in replaced]!r}
for uuid, object_path in entries:
    obj = s.GetPrimAtPath(object_path)
    replacement = s.GetPrimAtPath(obj.GetParent().GetPath().AppendChild(
        "RoomTwinReplacement_" + uuid.replace("-", "")))
    inverse = cache.GetLocalToWorldTransform(replacement).GetInverse()
    points = [inverse.Transform(cache.GetLocalToWorldTransform(mesh).Transform(Gf.Vec3d(point)))
              for mesh in Usd.PrimRange(replacement) if mesh.IsA(UsdGeom.Mesh)
              for point in (UsdGeom.Mesh(mesh).GetPointsAttr().Get() or [])]
    center = [((min(point[i] for point in points) + max(point[i] for point in points)) / 2)
              for i in range(3)]
    assert max(abs(center[i]) for i in range(3)) < 0.005, (uuid, center)
'''
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


def _staged_pair(tmp_path, usdz=b"new-usdz", report=b"new-report"):
    staged_usdz = tmp_path / "staged.usdz"
    staged_report = tmp_path / "staged.json"
    staged_usdz.write_bytes(usdz)
    staged_report.write_bytes(report)
    return staged_usdz, staged_report


def test_pair_publication_success_and_no_force_refusal(tmp_path):
    staged_usdz, staged_report = _staged_pair(tmp_path)
    output, report = tmp_path / "out.usdz", tmp_path / "out.json"
    publication.publish_output_pair(staged_usdz, staged_report, output, report, overwrite=False)
    assert output.read_bytes() == b"new-usdz"
    assert report.read_bytes() == b"new-report"

    staged_usdz, staged_report = _staged_pair(tmp_path, b"second-usdz", b"second-report")
    with pytest.raises(publication.PublicationError, match="already exists"):
        publication.publish_output_pair(staged_usdz, staged_report, output, report, overwrite=False)
    assert output.read_bytes() == b"new-usdz"
    assert report.read_bytes() == b"new-report"


def test_pair_publication_force_overwrites_both(tmp_path):
    output, report = tmp_path / "out.usdz", tmp_path / "out.json"
    output.write_bytes(b"old-usdz")
    report.write_bytes(b"old-report")
    staged_usdz, staged_report = _staged_pair(tmp_path)
    publication.publish_output_pair(staged_usdz, staged_report, output, report, overwrite=True)
    assert output.read_bytes() == b"new-usdz"
    assert report.read_bytes() == b"new-report"
    assert not list(tmp_path.glob("*.backup"))
    assert not list(tmp_path.glob(".*.backup"))


@pytest.mark.parametrize("fail_target", ["usdz", "report"])
def test_pair_publication_failure_restores_prior_pair_and_cleans_backups(
    tmp_path, monkeypatch, fail_target
):
    output, report = tmp_path / "out.usdz", tmp_path / "out.json"
    output.write_bytes(b"old-usdz")
    report.write_bytes(b"old-report")
    staged_usdz, staged_report = _staged_pair(tmp_path)
    real_replace = publication.os.replace

    def fail_once(source, destination):
        source, destination = Path(source), Path(destination)
        if fail_target == "usdz" and source == staged_usdz:
            raise OSError("injected USDZ publication failure")
        if fail_target == "report" and source == staged_report:
            raise OSError("injected report publication failure")
        return real_replace(source, destination)

    monkeypatch.setattr(publication.os, "replace", fail_once)
    with pytest.raises(publication.PublicationError, match="injected"):
        publication.publish_output_pair(staged_usdz, staged_report, output, report, overwrite=True)
    assert output.read_bytes() == b"old-usdz"
    assert report.read_bytes() == b"old-report"
    assert not list(tmp_path.glob(".*.backup"))
    assert list(tmp_path.glob("staged.*"))


@pytest.mark.parametrize("failure", ["package", "report"])
def test_cli_generation_failure_preserves_existing_pair(tmp_path, monkeypatch, capsys, failure):
    import app.usd.cli as cli
    output, report = tmp_path / "kept.usdz", tmp_path / "kept.report.json"
    output.write_bytes(b"old-usdz")
    report.write_bytes(b"old-report")
    if failure == "package":
        monkeypatch.setattr(cli, "package_usdz", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("package injected")))
    else:
        monkeypatch.setattr(cli, "_report", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("report injected")))
    code = main(["replace", "--usdz", str(SOURCE), "--json", str(SCAN), "--output", str(output),
                 "--force"])
    assert code == 1
    assert failure + " injected" in capsys.readouterr().err
    assert output.read_bytes() == b"old-usdz"
    assert report.read_bytes() == b"old-report"
    assert not list(tmp_path.glob("room-twin-work-*"))
    assert not list(tmp_path.glob("room-twin-stage-*"))


def test_cli_validation_failure_cannot_publish_or_misreport(tmp_path, monkeypatch, capsys):
    import app.usd.cli as cli
    from app.usd.packaging import ValidationResult
    output, report = tmp_path / "kept.usdz", tmp_path / "kept.report.json"
    output.write_bytes(b"old-usdz")
    report.write_bytes(b"old-report")

    def fake_package(result, path, **kwargs):
        Path(path).write_bytes(b"invalid-stage")
        return Path(path)

    monkeypatch.setattr(cli, "package_usdz", fake_package)
    monkeypatch.setattr(cli, "validate_usdz", lambda *a, **k: ValidationResult(
        False, None, ("unresolved dependency: missing.usdc",)))
    status = main(["replace", "--usdz", str(SOURCE), "--json", str(SCAN),
                   "--output", str(output), "--force"])
    assert status == 1
    assert "staged USDZ failed validation" in capsys.readouterr().err
    assert output.read_bytes() == b"old-usdz"
    assert report.read_bytes() == b"old-report"
    assert not list(tmp_path.glob("room-twin-stage-*"))
