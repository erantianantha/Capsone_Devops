# PantryPal Demo & Presentation

This directory contains the project presentation deck and recorded demonstration videos for the DevOps Capstone submission.

## Contents

| Item | File | Description |
|---|---|---|
| **Presentation Deck** | [`PantryPal-Presentation.pptx`](PantryPal-Presentation.pptx) | Final slide deck covering architecture, tech stack, CI/CD pipeline, DevSecOps, infrastructure as code (Terraform), Kubernetes deployment with Helm, observability (Prometheus & Grafana), and key project takeaways. |
| **Live Rollout Recording** | [`pantrypal-live-rollout.mp4`](pantrypal-live-rollout.mp4) | 64-second screen recording showing a live commit (`5381442`) travelling through GitHub Actions (lint, test, Trivy scan, GHCR build/push, kind deploy) and rolling out to the cluster without downtime via Helm. |
| **Project Walkthrough** | [`pantrypal-walkthrough.mp4`](pantrypal-walkthrough.mp4) | Comprehensive narrated video walkthrough (2½ min) explaining the end-to-end architecture, API, security gates, Terraform mock AWS setup, Helm chart release, and Grafana monitoring. |

---

For step-by-step instructions to reproduce the live rollout locally, see [`../docs/demo.md`](../docs/demo.md).
