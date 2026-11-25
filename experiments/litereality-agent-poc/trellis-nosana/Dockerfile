FROM nvidia/cuda:12.8.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TORCH_CUDA_ARCH_LIST=12.0 \
    CMAKE_CUDA_ARCHITECTURES=120 \
    CUDA_HOME=/usr/local/cuda \
    OPENCV_IO_ENABLE_OPENEXR=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    ATTN_BACKEND=sdpa \
    SPARSE_ATTN_BACKEND=xformers \
    HF_HOME=/cache/weights \
    HUGGINGFACE_HUB_CACHE=/cache/weights/hub \
    HF_HUB_DISABLE_IMPLICIT_TOKEN=1 \
    TORCH_HOME=/cache/weights/torch \
    LITEREALITY_WEIGHTS=/cache/weights \
    LITEREALITY_DINOV3=/cache/weights/dinov3 \
    LR_REPO_ROOT=/opt/litereality-agent \
    OUTPUT_DIR=/public

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates git git-lfs curl python3.10 python3.10-dev \
      python3-pip python3-venv libgl1 libglib2.0-0 libjpeg-dev libopenexr-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python3.10 -m pip install --upgrade pip setuptools wheel

WORKDIR /opt
ARG LITEREALITY_COMMIT=28ffe1fd4a1b03c93f1877a33a8bc9b806f72fe1
RUN git clone --filter=blob:none https://github.com/LiteReality/LiteReality-Agent.git /opt/litereality-agent \
    && git -C /opt/litereality-agent checkout "${LITEREALITY_COMMIT}" \
    && git -C /opt/litereality-agent submodule update --init --recursive \
    && test -f /opt/litereality-agent/src/litereality_agent/models/trellis/inference.py

# runtime_env.py resolves REPO_ROOT / "TRELLIS.2". LR_REPO_ROOT deliberately makes
# REPO_ROOT /opt/litereality-agent, so the clone must live exactly at that child path.
ARG TRELLIS2_COMMIT=75fbf0183001ed9876c8dbb35de6b68552ee08bd
RUN git clone --filter=blob:none https://github.com/microsoft/TRELLIS.2.git /opt/litereality-agent/TRELLIS.2 \
    && git -C /opt/litereality-agent/TRELLIS.2 checkout "${TRELLIS2_COMMIT}" \
    && git -C /opt/litereality-agent/TRELLIS.2 submodule update --init --recursive \
    && test -f /opt/litereality-agent/TRELLIS.2/assets/example_image/T.png

ENV PATH=/usr/local/bin:$PATH MAX_JOBS=2
RUN ln -sf /usr/bin/python3.10 /usr/local/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/local/bin/python3 \
    && python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --index-url https://download.pytorch.org/whl/cu128 \
         torch==2.9.1 torchvision==0.24.1 \
    && python -c 'import torch; assert torch.__version__.startswith("2.9.1+cu128"), torch.__version__; assert torch.version.cuda == "12.8", torch.version.cuda'

# Install the Python stack separately from the native xFormers build.
RUN python -m pip install \
         imageio imageio-ffmpeg tqdm easydict ninja \
         trimesh transformers==4.57.5 gradio==6.2.0 tensorboard pandas lpips zstandard \
         scipy timm kornia huggingface_hub safetensors pillow pydantic pydantic-settings rich \
         "git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8" \
    && python -m pip install -e /opt/litereality-agent \
    && python -c 'import torch; assert torch.__version__.startswith("2.9.1+cu128"), torch.__version__; assert torch.version.cuda == "12.8", torch.version.cuda'

# xFormers builds the CUDA operators used for sparse attention in its own cached
# layer. No dependency resolution is allowed to change the pinned PyTorch runtime.
RUN python -m pip install --no-deps --no-build-isolation --no-binary=xformers xformers==0.0.33.post2 \
    && python -c 'import torch; assert torch.__version__.startswith("2.9.1+cu128"), torch.__version__; assert torch.version.cuda == "12.8", torch.version.cuda'

# Fetch each native extension at an immutable commit. Each compile has its own cached
# Docker layer, so a change to one extension does not rebuild the other CUDA extensions.
WORKDIR /tmp/extensions
ARG NVDIFFRAST_COMMIT=253ac4fcea7de5f396371124af597e6cc957bfae
RUN git clone https://github.com/NVlabs/nvdiffrast.git nvdiffrast \
    && git -C nvdiffrast checkout "${NVDIFFRAST_COMMIT}"
RUN python -m pip install --no-deps --no-build-isolation ./nvdiffrast

ARG CUMESH_COMMIT=12289e1062f0603f2f0d0771b02e1395d247f26f
RUN git clone --recursive https://github.com/JeffreyXiang/CuMesh.git CuMesh \
    && git -C CuMesh checkout "${CUMESH_COMMIT}" \
    && git -C CuMesh submodule update --init --recursive
RUN python -m pip install --no-deps --no-build-isolation ./CuMesh

ARG FLEXGEMM_COMMIT=6dd94a859c26ee8246888502eada3dd8ad85532e
RUN git clone --recursive https://github.com/JeffreyXiang/FlexGEMM.git FlexGEMM \
    && git -C FlexGEMM checkout "${FLEXGEMM_COMMIT}" \
    && git -C FlexGEMM submodule update --init --recursive
RUN python -m pip install --no-deps --no-build-isolation ./FlexGEMM

ENV TRELLIS2_COMMIT=${TRELLIS2_COMMIT} \
    NVDIFFRAST_COMMIT=${NVDIFFRAST_COMMIT} \
    CUMESH_COMMIT=${CUMESH_COMMIT} \
    FLEXGEMM_COMMIT=${FLEXGEMM_COMMIT}

# nvdiffrec/renderutils is only imported by TRELLIS.2 training and texturing
# utilities, not the canonical image-to-GLB inference module. Leave it out.
WORKDIR /opt/litereality-agent/TRELLIS.2
RUN python -m pip install --no-deps --no-build-isolation ./o-voxel

COPY smoke_test.py cpu_verify.py /opt/trellis-nosana/
WORKDIR /opt/trellis-nosana
RUN python -m py_compile smoke_test.py cpu_verify.py \
    && python -m pip install pydantic==2.12.5 \
    && python -c 'import torch; assert torch.__version__.startswith("2.9.1+cu128"), torch.__version__; assert torch.version.cuda == "12.8", torch.version.cuda' \
    && python cpu_verify.py \
    && python -m pip check \
    && mkdir -p /cache/weights /public
EXPOSE 8000
ENTRYPOINT ["python", "/opt/trellis-nosana/smoke_test.py"]
