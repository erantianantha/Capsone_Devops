# M6 — Trivy security scan

## What runs in the pipeline

The `image` job in [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml) builds the backend and
frontend images, then runs Trivy (official `aquasec/trivy:0.76.0` container, version-pinned) against each
image **before** it is pushed to GHCR:

```
trivy image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 <image>:<git-sha>
```

`--exit-code 1` makes the step — and therefore the whole pipeline — fail if any HIGH or CRITICAL
vulnerability with an available fix is found, so a vulnerable image never reaches the registry.
The report is printed in the job log, added to the run's step summary and uploaded as an artifact.

## Result explanation (2–3 sentences)

Trivy scanned both images' OS packages (Debian 13 for the backend, Alpine 3.23 for the frontend) and every
Python library in the backend's virtualenv against its vulnerability databases. The current images come back
**clean — 0 fixable HIGH/CRITICAL CVEs** — so the gate passes and the images are pushed. That clean result
came from fixing real findings: the first backend build failed the gate on 4 HIGH issues, for example
**CVE-2025-47273**, a path-traversal bug in `setuptools` 70.3.0's `PackageIndex` that lets a crafted package
URL write files outside the target directory. We removed it by deleting `pip`/`setuptools` and the bundled
`ensurepip` wheels from the runtime image, since installing packages is only needed in the build stage.

## Before / after

| Image | Before hardening | After hardening |
|-------|------------------|-----------------|
| backend | 4 HIGH: `setuptools` CVE-2025-47273, `urllib3` CVE-2026-97687 / CVE-2026-97689, `msgpack` GHSA-6v7p-g79w-8964 (all vendored inside pip) | 0 |
| frontend | HIGH CVEs in Alpine `pcre2`, `libxml2`, `tiff`, `util-linux` from an older base layer | 0 (added `apk upgrade --no-cache`) |

Screenshots: `docs/screenshots/m6-trivy-before-hardening-findings.png`,
`m6-trivy-scan-backend.png`, `m6-trivy-scan-frontend.png`.
