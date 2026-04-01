FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RUNPOD_VOLUME_PATH=/runpod-volume \
    RUNPOD_MODELS_ROOT=/runpod-volume/models \
    HF_HOME=/tmp/huggingface

WORKDIR /opt/runpod-s1-model-loader

COPY requirements.txt /tmp/runpod-s1-model-loader-requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r /tmp/runpod-s1-model-loader-requirements.txt

COPY scripts /opt/runpod-s1-model-loader/scripts

ENTRYPOINT ["python", "/opt/runpod-s1-model-loader/scripts/download_models_to_volume.py"]
