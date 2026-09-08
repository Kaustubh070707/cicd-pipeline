---
project: cicd-pipeline
track: devops
level: beginner-intermediate
started: 2026-09-09
shipped:
repo:
live:
---
# 1. What this project is
Non-technical: Auto-check, build and deploy app on every push with safety rollback.
Engineer: GitHub Actions -> lint/test/scan -> multi-stage Docker -> GHCR SHA tags -> K8s rolling deploy with probes.

# 2. Problem it solves
Every push to main is tested, scanned, built small, deployed zero-downtime, rolled back on failed health. Attaches to D1/D4.

# 3. Architecture
```
[push main] -> [lint+test] -> [Trivy scan] -> [docker build+push SHA] -> [deploy kind/K8s] -> [probes verify]
```
Components:
- docker -> multi-stage slim/distroless -> 1.1GB to ~180MB
- pipeline -> lint,test,build,scan,push,deploy -> fail fast order
- k8s -> Deployment+Service+probes+limits -> rolling + auto rollback
- secrets -> GitHub Secrets never committed

# 4. Key decisions and trade-offs
| Decision | Options I considered | What I chose | Why | What I gave up |
|---|---|---|---|---|
| Base image | full vs slim vs distroless | slim TBD | size vs debug shell |  |
| Tagging | latest vs SHA | SHA | rollback traceability | human readability |
| Cluster | kind vs free-tier managed | kind local first | free, reproducible | cloud realism |

# 5. Skills demonstrated
- [ ] Pipeline design evidence: `.github/workflows/ci.yml`
- [ ] Multi-stage builds evidence: `Dockerfile` + size before/after
- [ ] Scanning evidence: Trivy step blocking CVE
- [ ] K8s probes + rolling evidence: `k8s/deployment.yaml`
- [ ] Secrets evidence: GitHub Secrets, no .env committed
- [ ] Rollback evidence: screenshot + curl loop log

# 6. Numbers I measured
| Metric | Before | After | How I measured it |
|---|---|---|---|
| image size | 1.1GB naive TBD | 180MB target | docker images |
| deploy downtime | TBD | 0 dropped in curl loop | curl loop during rollout |

# 7. Things that broke and how I fixed them
1. Symptom:
   Cause:
   Fix:
   Lesson:

# 8. What I would do differently at 100x scale
- TBD: remote registry cache, signed images, progressive delivery
- TBD:
- TBD:

# 9. Interview answers I have rehearsed
Q: Why is tagging latest dangerous?
A:
Q: Readiness vs liveness - what breaks if swapped?
A:
Q: Error spike after deploy - rollback steps?
A:

# 10. Honest limitations
<What this does NOT do.>

# 11. How to run it
```bash
git clone <repo> && cd cicd-pipeline
docker build -t app:naive -f Dockerfile.naive . # record size
docker build -t app:slim . # record size
kind create cluster && kubectl apply -f k8s/
```

# 12. Credits
- https://github.com/bregman-arie/devops-exercises
- https://github.com/bregman-arie/devops-resources
- https://roadmap.sh/devops
