# TRELLIS.2 RTX 5080 feasibility smoke test

This isolated experiment runs one image-to-GLB inference on an RTX 5080 with 16
GB VRAM. It calls the canonical `litereality_agent.models.trellis.inference`
module from LiteReality-Agent commit
`28ffe1fd4a1b03c93f1877a33a8bc9b806f72fe1`; it does not change production
generation or the scan-conversion pipeline.

The image keeps CUDA 12.8.1, PyTorch 2.9.1 (`cu128`), Python 3.10 and
`TORCH_CUDA_ARCH_LIST=12.0` for Blackwell `sm_120`. Dense attention uses PyTorch
SDPA and sparse attention uses xFormers. xFormers, nvdiffrast, CuMesh, FlexGEMM
and O-Voxel are built in separate Docker layers so each extension is cached
independently. TRELLIS.2 and the native Git dependencies are pinned to immutable
commits. Gradio 6.2.0 and `pydantic==2.12.5` satisfy both the project’s
Google GenAI minimum and Gradio’s compatibility range.
nvdiffrec is omitted:
the pinned inference path imports none of its training/texturing renderutils.

The TRELLIS.2 checkout is at `/opt/litereality-agent/TRELLIS.2`, exactly where
the pinned `runtime_env.py` resolves `REPO_ROOT / "TRELLIS.2"`. `LR_REPO_ROOT`
sets the repository root to `/opt/litereality-agent`, while
`LITEREALITY_WEIGHTS`, `HF_HOME`, and the Hugging Face hub cache all point into
`/cache/weights`. Mount that volume to retain both the HF model snapshots and
the local model preparation directory (`trellis2_4b_local`). DINOv3 is stored
under `/cache/weights/dinov3`. Public model downloads run anonymously; no
Hugging Face login or token is required.

## Build and CPU verification

From this directory in PowerShell, choose an image name in your Docker Hub
namespace and build the full image. The build compiles extensions on the CPU
build host using nvcc, without GPU access.

```powershell
$Image = "docker.io/<docker-user>/trellis2-nosana:rtx5080-test"
docker build --progress=plain -t $Image .
```

The final build layer compile-checks `smoke_test.py`, imports the canonical
inference module and native extensions (FlexGEMM uses stubbed GPU metadata for
its import-time device query), verifies their shared libraries contain `sm_120`
code, checks the upstream public example image, exercises model path resolution
and a fixture DINOv3 config rewrite without downloading model files, and runs
`pip check`.
The smoke test itself does not execute during build.

Inspect the built image and run the same CPU verification explicitly:

```powershell
docker image inspect $Image --format '{{.Size}}'
docker run --rm --entrypoint python $Image /opt/trellis-nosana/cpu_verify.py
docker run --rm --entrypoint python $Image -m pip check
```

## Local GPU run

On a Linux host with NVIDIA Container Toolkit, run:

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
docker run --rm --gpus all `
  -p 8000:8000 `
  -v trellis-model-cache:/cache/weights `
  -v "${PWD}/artifacts:/public" `
  $Image
```

The first run downloads several GB and may take several minutes. On success,
`sample.glb` and `report.json` are written to `artifacts` and served on port
8000. The report distinguishes configured target VRAM from detected GPU model,
compute capability, total physical VRAM and measured peak allocated/reserved
VRAM. It records CUDA/PyTorch/Transformers and immutable native dependency
revisions, plus the resolved model snapshot revision. The run fails before
downloading weights if the detected device is not an RTX 5080 (`sm_120`); a
different GPU cannot count as RTX 5080 verification.

## Publish to Docker Hub and deploy with Nosana

The following PowerShell workflow builds, tags and pushes the image from your
own machine. Docker prompts you to authenticate to Docker Hub; no Nosana API key
or CLI is involved.

```powershell
$DockerHubUser = "<docker-user>"
$Image = "docker.io/${DockerHubUser}/trellis2-nosana:rtx5080-test"
docker login --username $DockerHubUser
docker build --progress=plain -t $Image .
docker push $Image

$Definition = Get-Content -Raw .\job.json | ConvertFrom-Json
$Definition.ops[0].args.image = $Image
$ConcreteJob = Join-Path $env:TEMP "trellis2-nosana-job.json"
$Definition | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 $ConcreteJob
Get-Content -Raw $ConcreteJob | Set-Clipboard
```

Open the [Nosana deployment dashboard](https://deploy.nosana.com/deployments/create),
choose **Create Deployment**, paste the copied job definition, and select the
RTX 5080 market. Set **Strategy: SIMPLE**, **Replicas: 1**, and **Container
Timeout: 30 minutes** (the maximum for this experiment). Review the displayed
rate and total spend before starting the deployment. Nosana documents these as
deployment settings in minutes, alongside the job definition; the job JSON
itself specifies the GPU container, exposed port 8000 and minimum 16 GB VRAM.
The dashboard signs deployment actions for your connected wallet, so this flow
does not need an API key.

When the job is running, open its dashboard endpoint and download both files
before the timeout. In PowerShell, set the endpoint shown by the dashboard:

```powershell
$Endpoint = "https://<deployment-endpoint>"
Invoke-WebRequest "$Endpoint/sample.glb" -OutFile .\sample.glb
Invoke-WebRequest "$Endpoint/report.json" -OutFile .\report.json
```

As soon as both downloads finish, click **Stop** in the deployment dashboard.
The 30-minute timeout is a backstop, not a reason to leave a completed GPU job
running.

## Model access and verification scope

TRELLIS.2-4B is a public Hugging Face repository. The canonical
`prepare_local_model(MODEL_ID)` downloads its snapshot and rewrites the
`pipeline.json` DINOv3 reference to the local, digest-verified ungated mirror
`camenduru/dinov3-vitl16-pretrain-lvd1689m` at revision
`3c276edd87d6f6e569ff0c4400e086807d0f3881`. The mirror model checksum is
`dcb2e45127cccbf1601e5f42fef165eea275c8e5213197e8dcf3f48822718179`. Meta's
DINOv3 license is saved next to the weights and applies to redistribution.

CPU verification confirms package installation, imports, configuration and
native compilation only. GPU compatibility remains unverified until this image
completes inference on an actual RTX 5080 and produces a valid GLB plus report.

## Nosana references

- [Job definition and container examples](https://learn.nosana.com/deployments/jobs/job-definition/intro.html)
- [Deployment options, timeout, replicas and strategy](https://learn.nosana.com/deployments/options.html)
- [Deployment lifecycle](https://learn.nosana.com/deployments/intro.html)
- [Dashboard deployment workflow](https://nosana.com/blog/visual-command-center-managing-deployments-with-nosanas-dashboard/)
