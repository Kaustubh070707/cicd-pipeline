from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="C1 pipeline demo service")

class AskRequest(BaseModel):
    question:str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"msg": "C1 pipeline demo service"}

@app.post("/ask")
def ask(payload:AskRequest):
    return {"question":payload.question, "answer":f"C1 stub answer: {payload.question}"}
