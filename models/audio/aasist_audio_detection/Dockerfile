FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for audio decoding (libsndfile, ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY sdk/ /app/sdk/
RUN pip install --no-cache-dir -e /app/sdk

COPY models/audio/aasist_audio_detection/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY models/audio/aasist_audio_detection/ /app/

ENV MODEL_PORT=8001
ENV PRELOAD_MODEL=false
ENV USE_GPU=false

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["python3", "detector.py"]
