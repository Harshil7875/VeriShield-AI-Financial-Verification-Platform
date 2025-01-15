from fastapi import FastAPI

app = FastAPI(title="VeriShield Phase 1")

@app.get("/health")
def health_check():
    return {"status": "OK"}
