# End-to-End CI/CD Pipeline

Automated delivery for the [RAG chatbot](../production-rag-chatbot): every push runs lint, tests, vulnerability scan, SHA-tagged build, and deploy with probe-based rollback.

## Pipeline

```
push/PR on main
 └─ lint-test: ruff check + pytest (3 contract tests)
 └─ build-scan-push: Docker build → Trivy scan (fail on CRITICAL/HIGH) → push ghcr.io:<sha>
 └─ deploy: rolling update, readiness/liveness probes, automatic rollback
```

* Images tagged by commit SHA, never `latest` — every deploy traces to one commit.
* Secrets via GitHub Secrets; nothing sensitive in the repo.
* `main` merges only through a green pipeline (branch protection).

## Status

![ci](https://github.com/Kaustubh070707/cicd-pipeline/actions/workflows/pipeline.yml/badge.svg)

## Repo layout

```
.github/workflows/pipeline.yml   pipeline definition
app/                        demo service (health + ask contract, replaced by D1 image at attach)
k8s/deployment.yaml         Deployment + Service with probes and limits
Dockerfile / Dockerfile.naive   slim vs baseline images
requirements.txt            runtime deps (shipped in image)
requirements-dev.txt        CI-only deps (ruff, pytest — never shipped)
```

## Run locally

```bash
python -m venv .venv && .venv/Scripts/Activate.ps1
pip install -r requirements-dev.txt
ruff check app/
pytest -q
```

## Attaching to D1

Build context repointed at the RAG service Dockerfile, same SHA-tag flow; deploy step targets the live service with `/health` + `/ask` smoke checks. Trivy block and rollback demos recorded in `SKILL.md`.

## Rollback runbook (proven)

Break: `/health` forced to HTTP 500 → push → lint-test green, build-scan-push green, **deploy red**:
`Waiting for deployment "app" rollout to finish: 0 of 2 updated replicas are available... error: timed out waiting for the condition` — probes held all broken pods out of service, exit 1.
Recover: `git revert` the break commit → push → all three jobs green. Rollback here is an ordinary commit, no heroics.
