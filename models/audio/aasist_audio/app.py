from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import tempfile
import os
try:
    from model import AASISTAudioDetector
except ImportError:
    from models.audio.aasist_audio.model import AASISTAudioDetector

app = FastAPI(title="AASIST Audio Detector")
detector = AASISTAudioDetector()
detector.load_model()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "aasist_audio",
        "version": "1.0"
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1] if file.filename else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        result = detector.predict(tmp_path)
        return JSONResponse(result.dict())
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("MODEL_PORT", 6001))
    uvicorn.run(app, host="0.0.0.0", port=port)
