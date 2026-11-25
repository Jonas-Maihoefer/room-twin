#!/usr/bin/env python3
"""Single-image TRELLIS.2 GPU feasibility run using LiteReality-Agent's pinned inference."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LITEREALITY_COMMIT = "28ffe1fd4a1b03c93f1877a33a8bc9b806f72fe1"
DINOV3_REPO = "camenduru/dinov3-vitl16-pretrain-lvd1689m"
DINOV3_REVISION = "3c276edd87d6f6e569ff0c4400e086807d0f3881"
DINOV3_SHA256 = "dcb2e45127cccbf1601e5f42fef165eea275c8e5213197e8dcf3f48822718179"
DINOV3_LICENSE_URL = "https://raw.githubusercontent.com/facebookresearch/dinov3/main/LICENSE.md"
MODEL_ID = "microsoft/TRELLIS.2-4B"


def ensure_dinov3() -> Path:
    """Fetch the pinned ungated mirror, verify its weights and include Meta's license."""
    from huggingface_hub import snapshot_download

    cache = Path(os.environ.get("HF_HOME", "/cache/huggingface"))
    dino_dir = Path(os.environ.get("LITEREALITY_DINOV3", cache / "dinov3"))
    dino_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=DINOV3_REPO,
        revision=DINOV3_REVISION,
        local_dir=str(dino_dir),
    )
    weights = dino_dir / "model.safetensors"
    if not weights.is_file():
        raise RuntimeError(f"Pinned DINOv3 weights missing: {weights}")
    digest = hashlib.sha256()
    with weights.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != DINOV3_SHA256:
        raise RuntimeError(
            f"DINOv3 checksum mismatch: expected {DINOV3_SHA256}, got {actual}"
        )

    license_path = dino_dir / "LICENSE.md"
    if not license_path.is_file():
        request = urllib.request.Request(
            DINOV3_LICENSE_URL, headers={"User-Agent": "trellis-nosana-smoke/1.0"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            license_path.write_bytes(response.read())
    os.environ["LITEREALITY_DINOV3"] = str(dino_dir)
    return dino_dir


def mesh_statistics(glb_path: Path) -> dict:
    import numpy as np
    import trimesh

    scene = trimesh.load(str(glb_path), force="scene")
    mesh = scene.dump(concatenate=True)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise RuntimeError("Generated GLB contains no triangle mesh geometry")

    vertices = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.faces)
    if not np.isfinite(vertices).all():
        raise RuntimeError("Generated mesh contains non-finite vertex coordinates")
    if faces.ndim != 2 or faces.shape[1] != 3:
        raise RuntimeError(f"Expected triangular faces, got face array shape {faces.shape}")
    if faces.min() < 0 or faces.max() >= len(vertices):
        raise RuntimeError("Generated mesh has out-of-range face indices")

    areas = np.asarray(mesh.area_faces)
    degenerate_faces = int((~np.isfinite(areas) | (areas <= 1e-12)).sum())
    if degenerate_faces:
        raise RuntimeError(f"Generated mesh has {degenerate_faces} degenerate triangles")

    components = mesh.split(only_watertight=False)
    component_faces = sorted((len(part.faces) for part in components), reverse=True)
    component_count = len(component_faces)
    largest_component_fraction = (
        component_faces[0] / len(faces) if component_faces else 0.0
    )
    isolated_vertices = int((np.bincount(faces.reshape(-1), minlength=len(vertices)) == 0).sum())
    if component_count > 256:
        raise RuntimeError(
            "Generated mesh is severely fragmented after TRELLIS.2/CuMesh remeshing: "
            f"{component_count} disconnected components"
        )

    return {
        "vertices": int(len(vertices)),
        "faces": int(len(faces)),
        "components": component_count,
        "largest_component_face_fraction": round(largest_component_fraction, 6),
        "isolated_vertices": isolated_vertices,
        "degenerate_faces": degenerate_faces,
        "watertight": bool(mesh.is_watertight),
        "bounds": np.asarray(mesh.bounds).tolist(),
        "area": float(mesh.area),
        "volume": float(mesh.volume) if mesh.is_watertight else None,
        "fragmentation_warning": component_count > 64
        or largest_component_fraction < 0.5,
        "remeshing": "upstream o_voxel / CuMesh (enabled by canonical inference)",
    }


def save_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def run() -> tuple[Path, Path]:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; run this container with NVIDIA GPU access")
    device = torch.cuda.current_device()
    gpu_name = torch.cuda.get_device_name(device)
    if "5080" not in gpu_name:
        print(f"[smoke] Note: detected {gpu_name}; requested feasibility target is RTX 5080")

    output_dir = Path(os.environ.get("OUTPUT_DIR", "/public"))
    output_dir.mkdir(parents=True, exist_ok=True)
    glb_path = output_dir / "sample.glb"
    report_path = output_dir / "report.json"
    report = {
        "status": "running",
        "upstream_commit": LITEREALITY_COMMIT,
        "model": MODEL_ID,
        "pipeline_type": "512",
        "low_vram_mode": True,
        "texture_size": 1024,
        "inference_processes": 1,
        "gpu_model": gpu_name,
        "cuda_version": torch.version.cuda,
        "pytorch_version": torch.__version__,
    }
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    try:
        dino_dir = ensure_dinov3()
        trellis_dir = Path(os.environ.get("TRELLIS2_DIR", "/opt/litereality-agent/backends/TRELLIS.2"))
        image_path = Path(os.environ.get("SMOKE_IMAGE", trellis_dir / "assets/example_image/T.png"))
        if not image_path.is_file():
            raise RuntimeError(f"Public upstream example image not found: {image_path}")

        # This is the canonical implementation from LiteReality-Agent at the pinned SHA.
        from litereality_agent.models.trellis.inference import load_pipeline, generate

        pipeline = load_pipeline(MODEL_ID, skip_rembg=True)
        if hasattr(pipeline, "low_vram") and not pipeline.low_vram:
            raise RuntimeError("LiteReality TRELLIS.2 pipeline did not enter low-VRAM mode")
        generate(
            pipeline,
            image_path,
            glb_path,
            seed=42,
            decimation_target=50000,
            texture_size=1024,
            pipeline_type="512",
        )
        torch.cuda.synchronize(device)
        if not glb_path.is_file() or glb_path.stat().st_size == 0:
            raise RuntimeError("Inference completed without a non-empty sample.glb")

        mesh = mesh_statistics(glb_path)
        report.update(
            {
                "status": "success",
                "runtime_seconds": round(time.perf_counter() - started, 3),
                "peak_allocated_vram_bytes": int(torch.cuda.max_memory_allocated(device)),
                "peak_reserved_vram_bytes": int(torch.cuda.max_memory_reserved(device)),
                "dinov3": {
                    "repository": DINOV3_REPO,
                    "revision": DINOV3_REVISION,
                    "model_sha256": DINOV3_SHA256,
                    "license_file": str(dino_dir / "LICENSE.md"),
                },
                "output": {
                    "file": glb_path.name,
                    "size_bytes": glb_path.stat().st_size,
                    "mesh": mesh,
                },
            }
        )
        save_report(report_path, report)
        print(json.dumps(report, indent=2), flush=True)
        return glb_path, report_path
    except Exception as exc:
        runtime_error = "CUDA" in str(exc).upper() or "CUDA" in type(exc).__name__.upper()
        oom = isinstance(exc, torch.cuda.OutOfMemoryError) or "OUT OF MEMORY" in str(exc).upper()
        report.update(
            {
                "status": "failed",
                "failure_kind": "out_of_memory" if oom else "cuda_error" if runtime_error else "inference_or_validation_error",
                "error": f"{type(exc).__name__}: {exc}",
                "runtime_seconds": round(time.perf_counter() - started, 3),
                "peak_allocated_vram_bytes": int(torch.cuda.max_memory_allocated(device)),
                "peak_reserved_vram_bytes": int(torch.cuda.max_memory_reserved(device)),
            }
        )
        save_report(report_path, report)
        print(f"[smoke] FAILED: {report['failure_kind']}: {report['error']}", file=sys.stderr)
        raise


class PublicArtifactsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, directory=os.environ.get("PUBLIC_SERVER_DIR", "/tmp/trellis-public"), **kwargs
        )


def main() -> int:
    try:
        glb_path, report_path = run()
    except Exception:
        return 1

    import shutil

    public_names = {glb_path.name, report_path.name}
    public_dir = Path(os.environ.get("PUBLIC_SERVER_DIR", "/tmp/trellis-public"))
    public_dir.mkdir(parents=True, exist_ok=True)
    for artifact in (glb_path, report_path):
        shutil.copy2(artifact, public_dir / artifact.name)
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), PublicArtifactsHandler)
    print(f"[smoke] artifacts ready; serving only {sorted(public_names)} on port {port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
