FROM nvidia/cuda:12.8.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TORCH_CUDA_ARCH_LIST=12.0 \
    CUDA_HOME=/usr/local/cuda \
    OPENCV_IO_ENABLE_OPENEXR=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    ATTN_BACKEND=sdpa \
    SPARSE_ATTN_BACKEND=xformers \
    HF_HOME=/cache/huggingface \
    WEIGHTS_DIR=/cache/weights \
    TRELLIS2_DIR=/opt/litereality-agent/backends/TRELLIS.2 \
    LITEREALITY_ROOT=/opt/litereality-agent \
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

# LiteReality's canonical local runtime expects TRELLIS.2 at this path. It is a
# separate upstream checkout (not a LiteReality git submodule).
ARG TRELLIS2_REF=main
RUN git clone --recursive --branch "${TRELLIS2_REF}" \
      https://github.com/microsoft/TRELLIS.2.git \
      /opt/litereality-agent/backends/TRELLIS.2 \
    && test -f /opt/litereality-agent/backends/TRELLIS.2/setup.sh

ENV PATH=/usr/local/bin:$PATH
RUN ln -sf /usr/bin/python3.10 /usr/local/bin/python \
    && ln -sf /usr/bin/python3.10 /usr/local/bin/python3 \
    && python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --index-url https://download.pytorch.org/whl/cu128 \
         torch==2.9.1 torchvision==0.24.1 \
    && python -m pip install --no-build-isolation --no-binary=xformers xformers==0.0.33.post2 \
    && python -m pip install \
         imageio imageio-ffmpeg tqdm easydict opencv-python-headless ninja \
         trimesh transformers gradio==6.0.1 tensorboard pandas lpips zstandard \
         scipy timm kornia huggingface_hub safetensors pillow \
         "git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8" \
    && python -m pip install --no-deps -e /opt/litereality-agent

# Build all native TRELLIS.2 CUDA extensions with nvcc. This is a compile-only
# stage: CUDA extension compilation does not require a GPU to be attached.
ENV MAX_JOBS=2
WORKDIR /opt/litereality-agent/backends/TRELLIS.2
RUN mkdir -p /tmp/extensions \
    && git clone -b v0.4.0 https://github.com/NVlabs/nvdiffrast.git /tmp/extensions/nvdiffrast \
    && python -m pip install --no-build-isolation /tmp/extensions/nvdiffrast \
    && git clone --recursive https://github.com/JeffreyXiang/CuMesh.git /tmp/extensions/CuMesh \
    && python -m pip install --no-build-isolation /tmp/extensions/CuMesh \
    && git clone --recursive https://github.com/JeffreyXiang/FlexGEMM.git /tmp/extensions/FlexGEMM \
    && python -m pip install --no-build-isolation /tmp/extensions/FlexGEMM \
    && python -m pip install --no-build-isolation ./o-voxel

COPY smoke_test.py /opt/trellis-nosana/smoke_test.py
WORKDIR /opt/trellis-nosana
RUN mkdir -p /cache/huggingface /cache/weights /public
EXPOSE 8000
ENTRYPOINT ["python", "/opt/trellis-nosana/smoke_test.py"]
