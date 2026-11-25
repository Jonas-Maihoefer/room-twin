#!/usr/bin/env python3
"""CPU-only checks for the inference image; deliberately performs no model download."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch


def main() -> None:
    import torch
    import transformers
    from litereality_agent.models import runtime_env
    from litereality_agent.models.trellis import inference

    expected_repo_root = Path(os.environ["LR_REPO_ROOT"]).resolve()
    assert torch.__version__.startswith("2.9.1+cu128"), torch.__version__
    assert torch.version.cuda == "12.8", torch.version.cuda
    assert transformers.__version__ == "4.57.5", transformers.__version__
    trellis_root = expected_repo_root / "TRELLIS.2"
    assert runtime_env.TRELLIS2_DIR.resolve() == trellis_root
    assert Path(os.environ["LITEREALITY_WEIGHTS"]).resolve() == runtime_env.WEIGHTS_DIR
    assert Path(os.environ["HF_HOME"]).resolve() == runtime_env.WEIGHTS_DIR

    # TRELLIS.2 may import FlexGEMM while loading its package. FlexGEMM queries
    # the active GPU name at import time, so supply metadata only; no CUDA op runs.
    with patch.object(torch.cuda, "is_available", return_value=True), patch.object(
        torch.cuda, "get_device_name", return_value="NVIDIA GeForce RTX 5080 (CPU import stub)"
    ):
        importlib.import_module("trellis2")
        importlib.import_module("flex_gemm")
    imported = ["trellis2", "flex_gemm (CUDA metadata stub; no GPU operation)"]
    for name in ("xformers", "nvdiffrast.torch", "cumesh", "o_voxel"):
        importlib.import_module(name)
        imported.append(name)

    extension_arches: dict[str, list[str]] = {}
    for package in ("xformers", "nvdiffrast.torch", "cumesh", "flex_gemm", "o_voxel"):
        spec = importlib.util.find_spec(package)
        assert spec is not None and spec.origin, f"Cannot locate installed package {package}"
        root = Path(spec.origin).parent
        libraries = sorted(root.rglob("*.so"))
        # nvdiffrast exposes its compiled Torch extension as a top-level module,
        # outside the nvdiffrast package directory.
        if package == "nvdiffrast.torch":
            native_spec = importlib.util.find_spec("_nvdiffrast_c")
            assert native_spec is not None and native_spec.origin, "Missing _nvdiffrast_c extension"
            libraries.append(Path(native_spec.origin))
        assert libraries, f"No compiled shared libraries found for {package}"
        inspected: list[str] = []
        for library in libraries:
            result = subprocess.run(
                ["cuobjdump", "--list-elf", str(library)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and "sm_120" in result.stdout:
                inspected.append(library.name)
        assert inspected, f"No sm_120 CUDA binary found in {package}: {libraries}"
        extension_arches[package] = inspected

    example = trellis_root / "assets/example_image/T.png"
    assert example.is_file() and example.stat().st_size > 0, f"Missing public example: {example}"

    # Exercise upstream model config preparation against a tiny fixture so this test
    # verifies the DINO path rewrite without downloading weights or initializing CUDA.
    with tempfile.TemporaryDirectory(prefix="trellis-cpu-verify-") as temporary:
        root = Path(temporary)
        snapshot = root / "snapshots" / "test-model-revision"
        (snapshot / "ckpts").mkdir(parents=True)
        (snapshot / "pipeline.json").write_text(
            json.dumps({"args": {"image_cond_model": {"args": {"model_name": "gated"}}}}),
            encoding="utf-8",
        )
        dino_dir = root / "public-dinov3"
        dino_dir.mkdir()
        import huggingface_hub

        original_snapshot_download = huggingface_hub.snapshot_download

        def fixture_snapshot_download(repo_id: str) -> str:
            assert repo_id == "microsoft/TRELLIS.2-4B"
            return str(snapshot)

        huggingface_hub.snapshot_download = fixture_snapshot_download
        original_dinov3 = os.environ.get("LITEREALITY_DINOV3")
        original_local_model_dir = runtime_env.LOCAL_MODEL_DIR
        os.environ["LITEREALITY_DINOV3"] = str(dino_dir)
        runtime_env.LOCAL_MODEL_DIR = root / "prepared-model"
        try:
            prepared = Path(inference.prepare_local_model("microsoft/TRELLIS.2-4B"))
            rewritten = json.loads((prepared / "pipeline.json").read_text(encoding="utf-8"))
            actual_dino = rewritten["args"]["image_cond_model"]["args"]["model_name"]
            assert actual_dino == str(dino_dir.resolve())
            assert (prepared / "ckpts").resolve() == (snapshot / "ckpts").resolve()
        finally:
            if original_dinov3 is None:
                os.environ.pop("LITEREALITY_DINOV3", None)
            else:
                os.environ["LITEREALITY_DINOV3"] = original_dinov3
            runtime_env.LOCAL_MODEL_DIR = original_local_model_dir
            huggingface_hub.snapshot_download = original_snapshot_download

    print(
        json.dumps(
            {
                "status": "cpu_verified",
                "python": os.sys.version.split()[0],
                "torch": torch.__version__,
                "torch_cuda_build": torch.version.cuda,
                "torchvision": importlib.import_module("torchvision").__version__,
                "transformers": transformers.__version__,
                "canonical_inference_import": inference.__file__,
                "trellis2_root": str(trellis_root),
                "weights_root": str(runtime_env.WEIGHTS_DIR),
                "public_example_bytes": example.stat().st_size,
                "imports": imported,
                "sm_120_cuda_binaries": extension_arches,
                "model_config_rewrite": "passed (fixture, no download)",
                "cuda_available": torch.cuda.is_available(),
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
