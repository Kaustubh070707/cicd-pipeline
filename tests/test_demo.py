from fastapi.testclient import  TestClient

from app.main import app

client = TestClient(app)

def test_health_returns_ok():
    # DELIBERATE-BREAK (rollback demo): health is broken on purpose so the kind
    # rollout + smoke test fail. Revert to 200/ok immediately after the demo.
    response = client.get("/health")
    assert response.status_code == 500
    assert response.json() == {"status": "broken-for-rollback-demo"}

def test_root_returns_expected_shape():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert list(body) == ["msg"]
    assert isinstance(body["msg"],str)

def test_ask_returns_expected_shape():
    response = client.post("/ask",json={"question":"what is C1?"})
    assert response.status_code == 200
    body = response.json()
    assert list(body) == ["question", "answer"]
    assert body["question"] == "what is C1?"
    assert isinstance(body["answer"], str)