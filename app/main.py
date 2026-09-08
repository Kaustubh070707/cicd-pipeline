from fastapi import FastAPI
app = FastAPI(title="C1 demo app - replace with D1 image")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"msg": "C1 pipeline target - wire to D1 after D1 works"}
