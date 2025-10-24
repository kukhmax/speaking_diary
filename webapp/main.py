from fastapi import FastAPI

app = FastAPI(title="AI Voice Diary API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"name": "AI Voice Diary"}