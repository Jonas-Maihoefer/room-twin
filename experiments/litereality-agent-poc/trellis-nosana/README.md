# TRELLIS.2 RTX 5080 feasibility smoke test

This folder is an isolated Docker experiment for one image-to-GLB run on a 16 GB
RTX 5080. Inference calls `litereality_agent.models.trellis.inference` from the
LiteReality-Agent commit pinned in [`../UPSTREAM.md`](../UPSTREAM.md); it does not
change the scan-conversion pipeline or production OpenUSD backend.

The image uses CUDA 12.8.1, PyTorch 2.9.1 (`cu128`) and builds xFormers 0.0.33.post2
from source with `TORCH_CUDA_ARCH_LIST=12.0`. Dense attention is selected through
PyTorch SDPA (`ATTN_BACKEND=sdpa`); sparse attention uses xFormers
(`SPARSE_ATTN_BACKEND=xformers`). CUDA extensions are compiled with nvcc during
the Docker build. This is a CPU-side compile and does not require an NVIDIA GPU
on the build machine, although it does require Docker, network access and enough
RAM/disk for CUDA extension builds. This version combination is a feasibility
candidate; only a successful RTX 5080 run can establish runtime compatibility.

The smoke test uses TRELLIS.2-4B, `pipeline_type=512`, upstream low-VRAM mode,
texture size 1024, seed 42 and exactly one inference process. It uses the public
upstream example `backends/TRELLIS.2/assets/example_image/T.png`. TRELLIS.2 and
DINOv3 weights are downloaded at runtime and can persist in Docker volumes.
Nothing in the image cache is committed to Git.

## Build

Run these commands from this directory. Pick a registry/image name you can push
to; the same image can later run on an RTX 5080 workstation with NVIDIA Container
Toolkit installed.

```sh
IMAGE=docker.io/<docker-user>/trellis2-nosana:rtx5080-test
docker build --progress=plain -t "$IMAGE" .
```

The build fetches and checks out LiteReality-Agent commit
`28ffe1fd4a1b03c93f1877a33a8bc9b806f72fe1`, then separately clones Microsoft's
TRELLIS.2 repository into the path expected by that pinned inference code. The
TRELLIS.2 checkout defaults to its `main` branch (`--build-arg TRELLIS2_REF=...`
can select a tag or commit); the LiteReality inference wrapper itself remains
commit-pinned. It installs the Python stack, then compiles xFormers, nvdiffrast,
CuMesh, FlexGEMM and O-Voxel. The image build is not an inference test.

## Local RTX 5080 run

```sh
mkdir -p artifacts
docker run --rm --gpus all \
  -p 8000:8000 \
  -v trellis-hf-cache:/cache/huggingface \
  -v trellis-model-cache:/cache/weights \
  -v "$(pwd)/artifacts:/public" \
  "$IMAGE"
```

The first run downloads several GB of model files and can take time. After a
successful run, the container serves only `sample.glb` and `report.json` at
`http://localhost:8000/`; the same two files are written to `./artifacts/`.
The JSON report records the detected GPU, CUDA and PyTorch versions, peak
allocated and reserved VRAM, total cold-run time, output size, mesh statistics,
and DINOv3 revision/checksum. The container exits non-zero for missing CUDA,
CUDA/runtime errors, out-of-memory, missing/empty output, invalid triangle
geometry or severe fragmentation. A fragmentation warning is recorded for
less severe disconnected output. CuMesh/O-Voxel remeshing is performed by the
canonical upstream inference function and its resulting geometry is validated.

For PowerShell, replace `$(pwd)` with `${PWD}` in the bind mount argument.

## Push and run on Nosana

Push only after the local image build succeeds:

```sh
docker push "$IMAGE"
```

`job.json` is a Nosana v0.1 container job. It requests a GPU with at least 16 GB
VRAM and exposes port 8000. Set the image name in the environment and render a
concrete JSON file before posting:

```sh
export TRELLIS_NOSANA_IMAGE="$IMAGE"
envsubst < job.json > /tmp/trellis-nosana-job.json
nosana job post --file /tmp/trellis-nosana-job.json --market <RTX-5080-market>
```

Nosana charges for GPU execution. The command above is documentation only and
has not been run; confirm the selected market offers an RTX 5080 and inspect its
current rate before manually starting a job. This experiment does not submit or
start paid deployments automatically.

## DINOv3 license and weights

The pinned LiteReality configuration uses the ungated mirror
`camenduru/dinov3-vitl16-pretrain-lvd1689m` at revision
`3c276edd87d6f6e569ff0c4400e086807d0f3881`. The run hashes `model.safetensors`
against upstream's SHA-256
`dcb2e45127cccbf1601e5f42fef165eea275c8e5213197e8dcf3f48822718179` and fails
on mismatch. It also places Meta's current DINOv3 `LICENSE.md` in the local
weight directory next to the downloaded model. The DINOv3 License Agreement
applies; anyone redistributing the DINOv3 weights or derivatives must include a
copy of that agreement. The cache is runtime data and is not included in this
repository or the public artifact server. TRELLIS.2-4B is hosted publicly by
Microsoft and requires no Hugging Face login.

## Verification status

Keep the evidence levels distinct:

* **CPU-side build verification:** establishes dependency installation and
  CUDA extension compilation only. It does not establish GPU execution.
* **RTX 5080 inference verification:** requires a successful run on an actual
  RTX 5080 and a valid `sample.glb` plus `report.json`. No paid Nosana job is
  started as part of preparing this experiment.
