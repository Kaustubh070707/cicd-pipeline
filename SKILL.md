---
project: cicd-pipeline
track: devops
level: beginner-intermediate
started: 2026-09-09
shipped: 2026-09-25
repo: https://github.com/Kaustubh070707/cicd-pipeline
live: kind local (GHCR image ghcr.io/kaustubh070707/cicd-pipeline:sha) — no public URL; Railway deploy used for the RAG service sibling
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
- docker -> multi-stage slim (naive single-stage would be larger; actual demo image is small — see §6 for honest “not yet measured on this repo” note)
- pipeline -> lint,test,build,scan,push,deploy -> fail fast order
- k8s -> Deployment+Service+probes+limits -> rolling + auto rollback
- secrets -> GitHub Secrets never committed

# 4. Key decisions and trade-offs
| Decision | Options I considered | What I chose | Why | What I gave up |
|---|---|---|---|---|
| Base image | full vs slim vs distroless | slim | My demo builds small enough to pull in seconds and I can still open a shell to debug, which distroless would take away. Real sizes land in §6. | Shell-rich full image and the last bytes distroless would save. |
| Tagging | latest vs commit SHA | SHA | When the scan failed twice I could point at the exact commit in the tag. With latest I would never know which build was bad. | Tags a human can read at a glance. |
| Cluster | kind vs free-tier managed | kind local first | Free and I can break it on purpose without a bill. Cloud realism waits until D1 attach. | A public URL and managed control plane. |
| Trivy action pin | whatever README example said vs releases page | v0.36.0, verified on the releases page | My scaffold said 0.28.0 and the run died in 3 seconds resolving it. I stopped guessing tags after that and check releases first now. | Blind trust in tutorial pins. |
| Registry case | repo name as-is vs lowercased | Lowercased via a bash step | My owner name has a capital K and GHCR rejects capitals outright. GitHub expressions have no lowercase function, so a two-line bash step (`${GITHUB_REPOSITORY,,}`) makes `kaustubh070707/...` before build, scan, and push all use it. | A pure-YAML workflow with no shell tricks. |
| Scan scope | fail on everything vs ignore-unfixed | ignore-unfixed true | The first real scan found 44 HIGH in Debian packages with no fixed version published. Failing on those means red forever through no fault of mine. Now only fixable findings block. | The comfort of "zero findings" — my board will always show unfixable OS noise as accepted risk. |
| Starlette fix | leave fastapi 0.116.1 vs bump past the cap | Bumped fastapi to 0.135.2 plus explicit starlette==1.6.0 | Version 0.116.1 demands starlette under 0.48, so pip kept installing the vulnerable 0.47.3 even though patched releases existed. Worse, on my laptop pip saw 0.47.3 already there, said "already satisfied," and changed nothing — CI would have gone green while my machine stayed vulnerable. The explicit pin forces the upgrade everywhere. | Hands-off patching. Dependabot-style ranges would reintroduce the same silent-stale trap. |

# 5. Skills demonstrated
- [x] Pipeline design evidence: `.github/workflows/pipeline.yml` — lint-test gates build-scan-push via `needs`, push/deploy gated to `main` via `if`
- [x] Multi-stage builds evidence: `Dockerfile` + `Dockerfile.naive` (see §6 for sizing caveat — demo image not yet sized on this runner; RAG sibling verified 1.9GB→478MB with same pattern)
- [x] Scanning evidence: Trivy step at v0.36.0 blocking on CRITICAL/HIGH, `ignore-unfixed` scoped — first red (44 OS + 3 starlette) then green after pin bump
- [x] K8s probes + rolling evidence: `k8s/deployment.yaml` with readiness/liveness on `/health`, rolling update, resource limits; deploy green on kind (rollout + 20× curl smoke test)
- [x] Secrets evidence: `GITHUB_TOKEN` via secrets, `REPO_LC` computed not hardcoded, no .env committed
- [x] Rollback evidence: break-then-revert demo — deploy red with `0 of 2 available... timed out` (probes held), then green after `git revert`; screenshots and raw logs in `docs/`

# 6. Numbers I measured
| Metric | Before | After | How I measured it |
|---|---|---|---|
| pipeline health | lint green, build red (bad Trivy tag, then uppercase registry name) | 3/3 jobs green: lint-test 13s, build-scan-push 35s, deploy 10s | Actions tab per-commit checks, green-tick screenshot saved |
| scan findings | 44 HIGH debian OS + 3 HIGH starlette, push blocked | 0 fixable HIGHs, push + deploy ran | Trivy table in the job log before/after `ignore-unfixed` plus the fastapi/starlette bump |
| image size | not yet measured on this repo (demo app is tiny; RAG sibling with same pattern measured 1.9GB naive → 478MB slim) | slim vs naive delta to be recorded with `docker images` on next runner where Docker is available | `docker build -f Dockerfile.naive -t app:naive .` vs `docker build -t app:slim .` |
| deploy downtime | broken deploy: 0 of 2 replicas available, exit 1 | revert deploy: rollout green, 20× curl to `/health` all passed | `kubectl rollout status` + smoke loop in deploy job (`for i in $(seq 1 20); do curl -sf http://localhost:8000/health || exit 1; done`); raw logs in `docs/logs/` |

# 7. Things that broke and how I fixed them
1. Symptom: My first push went red in 3 seconds flat. The log said it could not resolve `aquasecurity/trivy-action@0.28.0`.
   Cause: I had copied that tag from an old example. The project had since moved every tag to a `v` prefix after a supply-chain incident, so 0.28.0 simply does not exist anymore. I confirmed v0.36.0 on the releases page instead of guessing another number.
   Fix: Pinned `aquasecurity/trivy-action@v0.36.0` in ci.yml and pushed again.
   Lesson: Never trust a version pin from a tutorial. Check the releases page first. Dead pins fail in seconds and look silly in a portfolio.
2. Symptom: With the tag fixed, the build step died instantly: repository name must be lowercase, pointing at `ghcr.io/Kaustubh070707/...`.
   Cause: My GitHub name has a capital K and registries only allow lowercase. I had built the tag straight from `github.repository`, which keeps the original case.
   Fix: Added a small bash step that writes the lowercased repo into `REPO_LC`, then used it in the build, scan, and push lines. Same SHA scheme, now spelled `kaustubh070707/...`.
   Lesson: GitHub's expression language has no lowercase function, so some things genuinely need two lines of shell. I learned to read the exact error instead of blaming Docker.
3. Symptom: First real scan went red with 44 HIGH in Debian packages plus 3 HIGH in starlette, blocking push and deploy. It felt like the gate could never go green.
   Cause: Two different problems wearing one red badge. The 44 OS findings had no fixed version published at all — unfixable base-image noise. The 3 starlette ones did have fixes, but my own `fastapi==0.116.1` demanded starlette under 0.48, so pip kept installing the vulnerable 0.47.3. And on my laptop pip even said "already satisfied" and changed nothing, which would have let CI go green while my machine stayed vulnerable.
   Fix: Set `ignore-unfixed: true` so only fixable findings block, bumped fastapi to 0.135.2 (cap gone), and pinned starlette==1.6.0 explicitly so every environment must upgrade. Next scan showed zero fixable HIGHs and the pipeline went 3/3 green.
   Lesson: `ignore-unfixed` hides what cannot be fixed; a version bump fixes what can. Never let the first cover up the second or the pipeline lies. And I check the whole advisory list now — my first "already patched" call was wrong because I had only looked at one CVE out of three.

# 8. What I would do differently at 100x scale
- Use a remote registry cache (GHCR cache or Buildx `--cache-from`) and signed images (cosign) so every commit does not rebuild the world and supply-chain is verifiable.
- Move to progressive delivery: canary or blue/green with automated health-analysis (Argo Rollouts) instead of plain rolling update, to catch error-rate spikes before 100% traffic shifts.
- Split the monolithic pipeline into build-test vs deploy workflows with environment protection rules and required reviewers, so deploys become a manual approval gate rather than auto on every push.

# 9. Interview answers I have rehearsed
Q: Why is tagging latest dangerous?
A: Latest moves on every push, so you can never say which code is live or roll back to the exact bad build. I tag every image with the commit SHA (`ghcr.io/...:<sha>`) and deploy that SHA. If scan or deploy fails, I know the commit and `git revert` is the rollback — no manual retagging.
Q: Readiness vs liveness — what breaks if swapped?
A: Readiness tells Kubernetes when to send traffic; liveness tells it when to restart. If you swap them, a slow-starting pod gets killed by liveness before it is ready, and a truly dead pod keeps getting traffic because readiness never restarts it. In my manifests readiness fails fast (5s period) to hold broken pods out of the Service, liveness is slower (15s) to avoid flapping.
Q: Error spike after deploy — rollback steps?
A: I do not roll back the cluster directly. I revert the bad commit on `main` and push. The pipeline builds the previous SHA again, scans it, pushes it, and the deploy job does a rolling update back. Proven here: I forced `/health` to 500, the rollout timed out at `0 of 2 available`, the job went red; `git revert` then went 3/3 green. Ordinary commit, not heroics.

# 10. Honest limitations
This is a CI-to-kind demo, not production. It has no external ingress, no persistent registry auth beyond `GITHUB_TOKEN`, no branch protection required yet, and three contract tests (health + ask shape). The RAG service sibling holds the real eval (29/30) and live URL; this repo proves the delivery mechanics that ship it.

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
