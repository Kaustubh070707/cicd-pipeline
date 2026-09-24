# End-to-End CI/CD Pipeline

Automated delivery for the [RAG chatbot](https://github.com/Kaustubh070707/production-rag-chatbot) — the sibling project that actually answers questions. This repo is the delivery side: every push runs lint, tests, vulnerability scan, SHA-tagged build, and deploy with probe-based rollback.

## Pipeline

```
push/PR on main
 └─ lint-test: ruff check + pytest
 └─ build-scan-push: Docker build → Trivy scan (fail on fixable CRITICAL/HIGH) → push ghcr.io:<sha>
 └─ deploy: rolling update, readiness/liveness probes, automatic rollback
```

* Images tagged by commit SHA, never `latest` — every deploy traces to one commit.
* Secrets via GitHub Secrets; nothing sensitive in the repo.
* `main` merges through a green pipeline. Branch protection requiring those checks is the next hardening step — to enable it, set the branch rule to require `lint-test`, `build-scan-push`, and `deploy` before merging.
* Trivy uses `ignore-unfixed: true` — only findings with a published fix can block. The first scan found 44 unfixable OS findings plus 3 fixable starlette ones; the flag drops the noise so the three were fixed explicitly.

## Status

[![ci](https://github.com/Kaustubh070707/cicd-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Kaustubh070707/cicd-pipeline/actions/workflows/pipeline.yml)

## What the demo app is

A tiny FastAPI service with `GET /health` (probed by Kubernetes) and `POST /ask` (mirrors the RAG service contract). It exists only so the pipeline has something real to lint, test, scan, and deploy — the RAG chatbot replaces it when the pipeline is generalized.

One real example tag: `ghcr.io/kaustubh070707/cicd-pipeline:9bfce73` (lowercased repo, commit SHA).

## Repo layout

```
.github/workflows/pipeline.yml   pipeline definition
app/                        tiny demo service (/health + /ask)
k8s/deployment.yaml         Deployment + Service with probes and limits
tests/                      contract tests (health + ask shape)
SKILL.md                    engineering log — decisions, numbers, failures, interview answers
Dockerfile / Dockerfile.naive   slim vs baseline images
docs/                       proof screenshots and raw deploy logs
requirements.txt            runtime deps (shipped in image)
requirements-dev.txt        CI-only deps (ruff, pytest — never shipped)
```

## Run locally

```bash
# Windows (PowerShell)
python -m venv .venv && .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
ruff check app/
pytest -q
# Linux / macOS
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check app/
pytest -q
```

## How it connects to the RAG service

The same pipeline shape ships the RAG chatbot by pointing the Docker build context at that repo's `Dockerfile` and running the same SHA-tag flow; the deploy smoke checks there are `/health` and `/ask`. The next hardening step is to generalize the workflow so the same file can ship either repo.

## Rollback runbook (proven)

Break: `/health` forced to HTTP 500 → push → lint-test green, build-scan-push green, **deploy red**:
`Waiting for deployment "app" rollout to finish: 0 of 2 updated replicas are available... error: timed out waiting for the condition` — probes held all broken pods out of service, exit 1.
Recover: `git revert` the break commit → push → all three jobs green.

## Proof

- `docs/all-green.png` — 3/3 jobs green (first full green: starlette pin past the CVE cap).
- `docs/probe-hold.png` — break pushed: 2 green, 1 failing (deploy red after 2m, probes held).
- `docs/logs/deploy-red.txt` + `docs/logs/deploy-green.txt` — full raw deploy logs for both runs.
