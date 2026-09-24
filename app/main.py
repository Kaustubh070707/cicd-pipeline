from fastapi import FastAPI, Response
from pydantic import BaseModel

app = FastAPI(title="C1 demo app - replace with D1 image")


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health(response: Response):
    response.status_code = 500
    return {"status": "broken-for-rollback-demo"}


@app.get("/")
def root():
    return {"msg": "C1 pipeline target - wire to D1 after D1 works"}


@app.post("/ask")
def ask(payload: AskRequest):
    return {"question": payload.question, "answer": f"C1 stub answer: {payload.question}"}
