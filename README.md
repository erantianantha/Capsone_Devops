# PantryPal — DevOps Capstone

**PantryPal** is a home pantry inventory tracker. You record what's in your kitchen — name, category,
quantity and unit, and an optional expiry date. PantryPal sorts everything by what expires first, flags
items expiring within 3 days or already expired, and shows summary stats so less food gets thrown away.

The app is a **React** frontend, a **FastAPI** backend and a **PostgreSQL** database. The rest of the
repository is the DevOps layer around it: tests, containers, CI/CD with a Trivy security gate, Terraform for
AWS, Kubernetes with Helm, and Prometheus + Grafana monitoring.

![PantryPal running in Kubernetes behind the Ingress](docs/screenshots/m8-app-via-ingress.png)

**Presentation:** [`PantryPal-Presentation.pptx`](PantryPal-Presentation.pptx) &nbsp;·&nbsp;
**Live rollout recording:** [`docs/video/pantrypal-live-rollout.mp4`](docs/video/pantrypal-live-rollout.mp4) &nbsp;·&nbsp;
**Video walkthrough (2½ min):** [`docs/video/pantrypal-walkthrough.mp4`](docs/video/pantrypal-walkthrough.mp4) &nbsp;·&nbsp;
**Evidence index:** [`docs/submission.md`](docs/submission.md) &nbsp;·&nbsp;
**Live demo script:** [`docs/demo.md`](docs/demo.md)

---

## Contents

1. [Architecture](#1-architecture)
2. [Tech stack](#2-tech-stack)
3. [Repository structure](#3-repository-structure)
4. [The application and its API](#4-the-application-and-its-api-m1)
5. [Run it: manually, then Docker, then Compose](#5-run-it-locally)
6. [Testing](#6-testing-m2)
7. [Git and GitHub](#7-git-and-github-m3)
8. [Docker](#8-docker-m4)
9. [CI/CD pipeline](#9-cicd-pipeline-m5)
10. [DevSecOps: Trivy](#10-devsecops-trivy-m6)
11. [Terraform: AWS VPC + EKS](#11-terraform-aws-vpc--eks-m7)
12. [Kubernetes + Helm](#12-kubernetes--helm-m8)
13. [Observability: Prometheus + Grafana](#13-observability-prometheus--grafana-m9)
14. [Live demo and cleanup](#14-live-demo-m10-and-cleanup)

---

## 1. Architecture

```mermaid
flowchart LR
  dev[Developer] -- git push main --> gh[GitHub Actions]
  gh -- "1 test (pytest, ruff)<br/>2 frontend build" --> gh
  gh -- "3 docker build → Trivy gate → push" --> ghcr[(GHCR<br/>images tagged :commit-sha)]
  gh -- "4 helm upgrade on kind + smoke test" --> k8s

  subgraph k8s[Kubernetes — namespace pantrypal]
    ing[Ingress<br/>Traefik] -- "/" --> fe[frontend ×2<br/>nginx + React]
    ing -- "/api" --> be[backend ×2<br/>FastAPI]
    be --> pg[(PostgreSQL<br/>StatefulSet + PVC)]
  end

  subgraph mon[namespace monitoring]
    prom[Prometheus] -- "scrape /metrics" --> be
    graf[Grafana] --> prom
  end

  tf[Terraform] -- "VPC · subnets · NAT · IAM · EKS · node group" --> aws[(AWS API)]
```

## 2. Tech stack

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | React 19 + Vite, served by unprivileged Nginx | Small static bundle; Nginx also proxies `/api` in Compose |
| Backend | FastAPI, SQLAlchemy 2, Pydantic 2 | Typed, fast, automatic OpenAPI docs at `/docs` |
| Database | PostgreSQL 16 + Alembic migrations | Relational data with versioned schema changes |
| Tests | pytest (19 tests) + ruff | Isolated SQLite test DB, so tests never touch Postgres |
| Containers | Multi-stage Dockerfiles, non-root users, Docker Compose | Small images, least privilege, one-command local stack |
| CI/CD | GitHub Actions → GHCR | Images tagged with the commit SHA; every commit is traceable |
| Security | Trivy | Pipeline fails on fixable HIGH/CRITICAL CVEs |
| IaC | Terraform (AWS provider 6.x) | VPC, 2 public and 2 private subnets, NAT, IAM, EKS + managed node group |
| Orchestration | Kubernetes (kind locally / EKS), Helm, Traefik Ingress | Declarative, repeatable deploys with rolling updates |
| Observability | prometheus-fastapi-instrumentator, Prometheus, Grafana | Request rate, latency percentiles, error rate per endpoint and pod |

## 3. Repository structure

```
.
├── backend/                 FastAPI app
│   ├── app/                 main.py, models.py, schemas.py, database.py, config.py, routers/items.py
│   ├── alembic/versions/    0001_create_pantry_items.py
│   ├── tests/               conftest.py, test_health.py, test_items.py
│   ├── Dockerfile           multi-stage, runs as uid 10001
│   ├── requirements.txt     runtime deps      requirements-dev.txt  + pytest, httpx, ruff
│   └── pytest.ini
├── frontend/                React app (src/), nginx/default.conf.template, multi-stage Dockerfile
├── docker-compose.yml       frontend :3000, backend :8000, postgres (volume + bridge network)
├── .github/workflows/       ci-cd.yml — test → build → Trivy → push → deploy
├── terraform/               main.tf, variables.tf, outputs.tf, versions.tf, tfvars example, mock-aws/
├── k8s/                     namespace.yaml, kind-config.yaml, traefik-values.yaml
├── helm/pantrypal/          Chart.yaml, values.yaml, values-dev.yaml, values-prod.yaml, templates/
├── monitoring/              prometheus-values.yaml, grafana-values.yaml, dashboards/pantrypal-api.json
├── scripts/                 setup-local-cluster.sh, generate-traffic.sh
├── docs/                    screenshots/, evidence/, security-scan.md, demo.md, submission.md
├── docs/video/              pantrypal-live-rollout.mp4 (commit → pipeline → rollout), pantrypal-walkthrough.mp4
└── PantryPal-Presentation.pptx
```

---

## 4. The application and its API (M1)

Features:
- Add pantry items with category, quantity, unit and optional expiry date
- Items sorted soonest-expiry first, with colour badges: expired, expiring within 3 days, OK, no expiry
- Inline +/− quantity buttons, edit and delete
- Search by name and filter by category
- Summary cards: items tracked, expiring soon, expired, number of categories
- A build badge showing the deployed commit SHA, which makes rollouts visible
- Responsive layout that works on phones

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health`, `/api/health` | Liveness, plus the deployed version (commit SHA) |
| GET | `/ready` | Readiness: returns 503 if the database is unreachable |
| GET | `/api/items?category=&search=` | List items, soonest expiry first |
| GET | `/api/items/{id}` | Get one item |
| POST | `/api/items` | Create an item |
| PUT | `/api/items/{id}` | Update an item (partial update) |
| DELETE | `/api/items/{id}` | Delete an item |
| GET | `/api/items/stats` | Totals, expiring soon, expired, counts by category |
| GET | `/api/categories` | Allowed categories |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | Swagger UI (interactive API docs) |

The database schema is created by **Alembic** (`backend/alembic/versions/0001_create_pantry_items.py`), which
the backend container runs on start-up. A Postgres advisory lock makes this safe when several replicas start at once.

| UI (desktop) | UI (mobile) |
|---|---|
| ![App on localhost:3000](docs/screenshots/m1-app-browser-localhost-3000.png) | ![Mobile layout](docs/screenshots/m1-app-mobile-view.png) |

**Backend endpoints:**

| `/docs` (Swagger) | Swagger "Try it out" (`GET /api/items/stats` → 200) |
|---|---|
| ![Swagger](docs/screenshots/m1-backend-swagger-docs.png) | ![Try it out](docs/screenshots/m1-backend-swagger-try-it-out.png) |

| `/health` | `/ready` |
|---|---|
| ![health](docs/screenshots/m1-backend-health.png) | ![ready](docs/screenshots/m1-backend-ready.png) |

`GET /api/items` (JSON straight from PostgreSQL):

![api items](docs/screenshots/m1-backend-api-items.png)

`/metrics` in the browser:

![metrics](docs/screenshots/m1-backend-metrics-browser.png)

Full CRUD with curl (POST → GET → PUT → DELETE → 404):

![CRUD with curl](docs/screenshots/m1-api-crud-curl.png)

---

## 5. Run it locally

### 5a. Manually (no Docker)

Prerequisites: Python 3.12+, Node 22+, and PostgreSQL running locally.

```bash
# 1. Database
createuser -P pantrypal          # password: pantrypal
createdb -O pantrypal pantrypal

# 2. Backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL="postgresql+psycopg://pantrypal:pantrypal@localhost:5432/pantrypal"
alembic upgrade head                       # create the tables
uvicorn app.main:app --reload --port 8000  # http://localhost:8000/docs

# 3. Frontend (terminal 2)
cd frontend
npm install
npm run dev                                # http://localhost:3000 (proxies /api to :8000)
```

### 5b. With plain Docker (one container at a time)

```bash
docker network create pantrypal-net
docker volume create pgdata

docker run -d --name postgres --network pantrypal-net -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_DB=pantrypal -e POSTGRES_USER=pantrypal -e POSTGRES_PASSWORD=pantrypal postgres:16-alpine

docker build -t pantrypal-backend ./backend
docker run -d --name backend --network pantrypal-net -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://pantrypal:pantrypal@postgres:5432/pantrypal pantrypal-backend

docker build -t pantrypal-frontend ./frontend
docker run -d --name frontend --network pantrypal-net -p 3000:8080 \
  -e BACKEND_URL=http://backend:8000 pantrypal-frontend
```

### 5c. With Docker Compose (recommended)

```bash
cp .env.example .env           # optional — defaults work for local dev
docker compose up --build      # or: docker compose up -d --build
docker compose ps
```

| URL | What |
|-----|------|
| <http://localhost:3000> | Frontend |
| <http://localhost:8000/docs> | Swagger UI |
| <http://localhost:8000/health> · `/ready` · `/metrics` | Health, readiness, metrics |

Compose starts `postgres` → `backend` → `frontend` in order, using `depends_on` with health conditions. Data
lives in the `pgdata` volume, and all three services share the `pantrypal-net` bridge network.

---

## 6. Testing (M2)

```bash
cd backend
pip install -r requirements-dev.txt
ruff check .     # lint
pytest -v        # 19 tests
```

- `tests/conftest.py` points the app at an **in-memory SQLite database** through a FastAPI dependency
  override, so tests never touch the real PostgreSQL.
- The tests cover health, readiness (including a simulated DB outage → 503), categories, metrics, and full
  CRUD on items: validation errors (422), 404s, filtering, expiry sorting and stats.

![pytest -v](docs/screenshots/m2-pytest-passing.png)

---

## 7. Git and GitHub (M3)

- Repository: <https://github.com/erantianantha/Capsone_Devops>
- Commits are small and descriptive, one logical change each.
- `.gitignore` excludes `.env`, `__pycache__/`, `node_modules/`, `.venv/`, Terraform state and `terraform.tfvars`.
- No credentials are in the repo. A Trivy secret scan of the repo is clean.

| GitHub repository | Commit history on GitHub |
|---|---|
| ![repo](docs/screenshots/m3-github-repo.png) | ![commits](docs/screenshots/m3-github-commits.png) |

`git log`:

![Commit history](docs/screenshots/m3-commit-history.png)

---

## 8. Docker (M4)

| Image | Build | Runtime user |
|-------|-------|--------------|
| `backend/Dockerfile` | Stage 1 builds a virtualenv; stage 2 is `python:3.12-slim` with only the venv and app code. pip/setuptools are removed and OS patches applied | `app` (uid 10001) |
| `frontend/Dockerfile` | Stage 1 `node:22-alpine` runs `npm ci && npm run build`; stage 2 `nginx-unprivileged:1.29-alpine` serves `dist/` | `nginx` (uid 101) |

Both images have a `HEALTHCHECK`, and both folders have a `.dockerignore`.

`docker compose up --build`:

![docker compose up --build](docs/screenshots/m4-docker-compose-up-build.png)

`docker compose ps` (all three services healthy):

![docker compose ps](docs/screenshots/m4-docker-compose-ps.png)

Browser at `http://localhost:3000`:

![localhost:3000](docs/screenshots/m4-browser-localhost-3000.png)

---

## 9. CI/CD pipeline (M5)

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) runs on **every push to `main`**, on pull requests and on demand:

| Stage | Job | What it does |
|-------|-----|--------------|
| 1 | **Backend lint + pytest** | `ruff check` + `pytest -v`. Any failing test fails the build |
| 1 | **Frontend build** | `npm ci && npm run build` |
| 2 | **Image (backend / frontend)** | `docker build` → **Trivy scan** (fails on HIGH/CRITICAL) → `docker push` to **GHCR** as `ghcr.io/<owner>/pantrypal-<component>:<commit-sha>`, never `latest` |
| 3 | **Deploy to kind** | Creates a throwaway kind cluster on the runner, pulls the new SHA images, installs Traefik + the Helm chart, and **smoke-tests through the Ingress**: health returns the new SHA, POST then GET an item, frontend serves HTML |
| 4 | Deploy to persistent cluster *(optional)* | Same Helm upgrade on a self-hosted runner, for the live demo. Enabled with `DEPLOY_ENABLED=true` |

Green pipeline run. Every job passed: test → build → Trivy → push → deploy to kind:

![GitHub Actions run](docs/screenshots/m5-github-actions-run.png)

| pytest in CI | Push to GHCR with the SHA tag |
|---|---|
| ![pytest in CI](docs/screenshots/m5-pipeline-pytest.png) | ![push](docs/screenshots/m5-pipeline-push-ghcr.png) |

Deploy stage: Helm install on kind, smoke test through the Ingress, cluster state:

![deploy to kind](docs/screenshots/m5-pipeline-deploy-kind-smoke-test.png)

Images in GHCR, tagged with commit SHAs (never `latest`). The packages are public:

| Packages | `pantrypal-backend` versions |
|---|---|
| ![GHCR packages](docs/screenshots/m5-ghcr-packages.png) | ![backend package](docs/screenshots/m5-ghcr-package-backend.png) |

`pantrypal-frontend` versions:

![frontend package](docs/screenshots/m5-ghcr-package-frontend.png)

All workflow runs:

![runs](docs/screenshots/m5-github-actions-history.png)

---

## 10. DevSecOps: Trivy (M6)

```yaml
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.76.0 image \
  --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 <image>:<sha>
```

`--exit-code 1` stops the pipeline before the push if any fixable HIGH/CRITICAL CVE is found.

**What the result means.** Trivy scans the OS packages (Debian 13 / Alpine 3.23) and every Python library in
the backend image. The current images are **clean: 0 fixable HIGH/CRITICAL CVEs**. They weren't at first. The
first backend build failed on 4 HIGH findings, e.g. **CVE-2025-47273**, a path-traversal bug in `setuptools`
70.3.0 that lets a crafted package URL write files outside the target directory. It was fixed by removing
pip/setuptools from the runtime image, since installing packages only happens in the build stage. Details:
[docs/security-scan.md](docs/security-scan.md).

| Pipeline scan | Before hardening (gate fails) |
|---|---|
| ![Trivy in pipeline](docs/screenshots/m6-trivy-pipeline.png) | ![Trivy findings](docs/screenshots/m6-trivy-before-hardening-findings.png) |

| Backend (clean) | Frontend (clean) |
|---|---|
| ![backend](docs/screenshots/m6-trivy-scan-backend.png) | ![frontend](docs/screenshots/m6-trivy-scan-frontend.png) |

---

## 11. Terraform: AWS VPC + EKS (M7)

| File | Contents |
|------|----------|
| `main.tf` | VPC, 2 public subnets and 2 private subnets in 2 AZs, Internet Gateway, NAT Gateway, route tables, IAM roles, **EKS cluster**, **managed node group** (2 × t3.medium, 1–3) |
| `variables.tf` | Region, CIDRs, AZs, Kubernetes version, node sizes, mock endpoint |
| `outputs.tf` | VPC/subnet IDs, cluster name/endpoint/status, `aws eks update-kubeconfig` command |
| `versions.tf` | Terraform + AWS provider version constraints and the provider configuration |
| `terraform.tfvars.example` | Example inputs. The real `terraform.tfvars` is git-ignored and **no credentials are committed** |

> **Mock AWS.** This project has no AWS account, so every AWS API call goes to a local
> [moto](https://github.com/getmoto/moto) server (`terraform/mock-aws/docker-compose.yml`). `init`, `plan`,
> `apply` and `destroy` all run for real against it at no cost. Setting `mock_aws_endpoint = ""` points the
> same code at real AWS.

```bash
docker compose -f terraform/mock-aws/docker-compose.yml up -d
cd terraform && cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan       # Plan: 25 to add
terraform apply tfplan
terraform destroy                # 25 destroyed
```

| `terraform init` | `terraform plan` (25 to add) |
|---|---|
| ![init](docs/screenshots/m7-terraform-init.png) | ![plan](docs/screenshots/m7-terraform-plan.png) |

| Planned resources | `terraform apply` |
|---|---|
| ![plan resources](docs/screenshots/m7-terraform-plan-resources.png) | ![apply](docs/screenshots/m7-terraform-apply.png) |

VPC, subnets, EKS cluster (ACTIVE) and node group, queried with the AWS CLI against the mock AWS endpoint:

![VPC and EKS](docs/screenshots/m7-aws-vpc-eks-mock-console.png)

`terraform destroy`, followed by a check that nothing is left:

![destroy](docs/screenshots/m7-terraform-destroy.png)

---

## 12. Kubernetes + Helm (M8)

Locally the chart runs on a **kind** cluster. On AWS it would run on the EKS cluster from section 11 with `values-prod.yaml`.

```bash
scripts/setup-local-cluster.sh       # kind + Traefik + build/load images + helm install + monitoring
# or step by step:
kind create cluster --config k8s/kind-config.yaml
kubectl apply -f k8s/namespace.yaml
helm upgrade --install traefik traefik/traefik -n ingress -f k8s/traefik-values.yaml
helm upgrade --install pantrypal ./helm/pantrypal -n pantrypal -f helm/pantrypal/values-dev.yaml \
  --set backend.image.tag=<sha> --set frontend.image.tag=<sha> --wait
```

The chart (`helm/pantrypal/`) contains:
- Backend and frontend **Deployments**, 2 replicas each, rolling updates with `maxUnavailable: 0`
- **ClusterIP Services** for the backend, frontend and PostgreSQL
- A PostgreSQL **StatefulSet** with a PVC, and a password **Secret** generated once and kept across upgrades
- An **Ingress**: `/` → frontend, `/api` → backend, host `pantrypal.localtest.me`
- Startup, readiness (`/ready`) and liveness (`/health`) probes, plus an init container that waits for the DB
- PodDisruptionBudgets and an optional HPA (enabled in `values-prod.yaml`)
- A non-root security context with all capabilities dropped

| `kubectl apply -f k8s/namespace.yaml` | `helm upgrade --install` |
|---|---|
| ![namespace](docs/screenshots/m8-kubectl-apply-namespace.png) | ![helm upgrade](docs/screenshots/m8-helm-upgrade-install.png) |

`kubectl get pods -n pantrypal` (all Running):

![pods](docs/screenshots/m8-kubectl-get-pods.png)

| `kubectl get svc -n pantrypal` | `helm list -n pantrypal` |
|---|---|
| ![svc](docs/screenshots/m8-kubectl-get-svc.png) | ![helm list](docs/screenshots/m8-helm-list.png) |

Ingress rules, Deployments and the StatefulSet:

![ingress](docs/screenshots/m8-kubectl-get-ingress-deploy.png)

App through the Ingress hostname, <http://pantrypal.localtest.me>. The build badge shows the deployed commit:

![app via ingress](docs/screenshots/m8-app-via-ingress.png)

---

## 13. Observability: Prometheus + Grafana (M9)

- The backend exposes `/metrics`. `prometheus-fastapi-instrumentator` adds `http_requests_total` (by handler,
  method and status) and the latency histograms.
- **Prometheus** (`monitoring/prometheus-values.yaml`) has a dedicated `pantrypal-backend` scrape job. It
  discovers backend pods by their Kubernetes labels and scrapes each one every 15s.
- **Grafana** (`monitoring/grafana-values.yaml`) is provisioned with the Prometheus data source and the
  *PantryPal API* dashboard (`monitoring/dashboards/pantrypal-api.json`). The dashboard shows request rate,
  p95 latency, 5xx error rate, pods UP, requests per endpoint, latency percentiles, responses by status class,
  and requests per pod. The admin password lives in a Kubernetes Secret, not in Git.

```bash
helm upgrade --install prometheus prometheus-community/prometheus -n monitoring -f monitoring/prometheus-values.yaml
helm upgrade --install grafana grafana/grafana -n monitoring -f monitoring/grafana-values.yaml \
  --set-file 'dashboards.default.pantrypal-api.json=monitoring/dashboards/pantrypal-api.json'
scripts/generate-traffic.sh http://pantrypal.localtest.me 300     # generate load
```

`curl /metrics` from the backend Service:

![curl metrics](docs/screenshots/m9-curl-backend-metrics.png)

Prometheus targets: `pantrypal-backend` 2/2 **UP**:

![targets](docs/screenshots/m9-prometheus-targets-up.png)

Grafana *PantryPal API* dashboard with live data:

![grafana](docs/screenshots/m9-grafana-dashboard.png)

| PromQL: requests/s by endpoint | Monitoring releases |
|---|---|
| ![query](docs/screenshots/m9-prometheus-query.png) | ![helm list -A](docs/screenshots/m9-helm-list-all-monitoring.png) |

---

## 14. Live demo (M10) and cleanup

Demo: **commit a change → watch the pipeline → see the deployment update.** This was recorded for real. The tagline
change in commit `5381442` was pushed to `main`. GitHub Actions tested, built, scanned and pushed the images, deployed
them to a fresh kind cluster, then rolled them out to the persistent cluster through a self-hosted runner. No manual
steps were needed.

▶ **Recording (64 s):** [`docs/video/pantrypal-live-rollout.mp4`](docs/video/pantrypal-live-rollout.mp4)

The pipeline run with all six jobs green, including *Deploy to persistent cluster (self-hosted)*:

![run with rollout](docs/screenshots/m10-pipeline-run-with-rollout.png)

| After the rollout: new tagline, build `5381442` | `helm history`: revision 5 deployed by the pipeline |
|---|---|
| ![app after](docs/screenshots/m10-app-after-rollout.png) | ![helm history](docs/screenshots/m10-helm-history-rollout.png) |

Step-by-step instructions to repeat it live are in [docs/demo.md](docs/demo.md).

A narrated walkthrough of the whole project (app → API → GitHub → CI/CD → GHCR → Trivy → Terraform →
Kubernetes → Prometheus → Grafana) is in [`docs/video/pantrypal-walkthrough.mp4`](docs/video/pantrypal-walkthrough.mp4).

Cleanup:

```bash
docker compose down -v
kind delete cluster --name pantrypal
cd terraform && terraform destroy && docker compose -f mock-aws/docker-compose.yml down
```
