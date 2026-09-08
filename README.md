# C1 End-to-End CI/CD Pipeline

> Highest ROI in vault. Attach to D1 flagship. Lint -> test -> scan -> build -> push -> deploy + rollback.

## Build order
1. Take D1 app. Write naive Dockerfile, record size.
2. Rewrite multi-stage slim/distroless, record delta for resume.
3. Actions workflow lint+test only. Green.
4. Add build+push SHA tags to GHCR.
5. Add Trivy scan, introduce vuln dep to confirm block.
6. K8s manifests: Deployment, Service, ConfigMap, Secret, probes, limits.
7. Deploy stage to kind, verify rolling with curl loop.
8. Break health check, confirm rollback. Screenshot + runbook.

## Image sizes
| Stage | Size |
|---|---|
| naive | TBD |
| slim | TBD target ~180MB |

## Gate
1. Why not `latest` tag?
2. Readiness vs liveness?
3. Rollback steps on error spike?

## Resume bullet template
Built GitHub Actions pipeline with Trivy, multi-stage Docker, K8s deploy; cut image 1.1GB->180MB, probe-based rollback verified under live traffic.
