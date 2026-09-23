FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg git && rm -rf /var/lib/apt/lists/*

COPY sdk/ /app/sdk/
RUN pip install --no-cache-dir /app/sdk/

COPY models/audio/aasist_audio/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY models/audio/aasist_audio/ /app/

ENV MODEL_PORT=6001

EXPOSE 6001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "6001"]
