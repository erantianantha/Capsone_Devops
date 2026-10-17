# Submission evidence index

GitHub repository: <https://github.com/erantianantha/Capsone_Devops>

All screenshots are in [`docs/screenshots/`](screenshots). Terminal screenshots are rendered from the
real command output. The raw Terraform output is kept in [`docs/evidence/`](evidence).

## M1 — Application
| Requirement | Evidence |
|---|---|
| Backend source (models, schemas, routes, DB config) | `backend/app/` |
| Alembic migration | `backend/alembic/versions/0001_create_pantry_items.py` |
| Requirements | `backend/requirements.txt` |
| Frontend source | `frontend/` |
| Stack definition | `docker-compose.yml` |
| App running in browser | `m1-app-browser-localhost-3000.png`, `m1-app-mobile-view.png` (responsive layout) |

## M2 — Testing
| Requirement | Evidence |
|---|---|
| Tests (17 cases across 7 endpoints) | `backend/tests/` |
| Config | `backend/pytest.ini`, `backend/tests/conftest.py` (SQLite test DB via dependency override) |
| `pytest -v` passing | `m2-pytest-passing.png` |

## M3 — Git and GitHub
| Requirement | Evidence |
|---|---|
| Repository URL | <https://github.com/erantianantha/Capsone_Devops> |
| Commit history (≥10 meaningful commits) | `m3-commit-history.png` |
| `.gitignore` (`.env`, `__pycache__`, `node_modules`, `.venv`, tfstate…) | `.gitignore` |

## M4 — Docker
| Requirement | Evidence |
|---|---|
| Backend Dockerfile (multi-stage, uid 10001) | `backend/Dockerfile` |
| Frontend Dockerfile (Node build → nginx-unprivileged, uid 101) | `frontend/Dockerfile` |
| `docker compose up --build` | `m4-docker-compose-up-build.png`, `m4-docker-compose-ps.png` |
| Browser at `http://localhost:3000` | `m4-browser-localhost-3000.png` |

## M5 — CI/CD
| Requirement | Evidence |
|---|---|
| Workflow | `.github/workflows/ci-cd.yml` |
| Green pipeline run | `m5-github-actions-run.png` + run URL in the submission form |
| GHCR packages with SHA tags | `m5-ghcr-packages.png` |

## M6 — DevSecOps
| Requirement | Evidence |
|---|---|
| Trivy step (fails on HIGH/CRITICAL) | `.github/workflows/ci-cd.yml` → "Trivy vulnerability scan" |
| Scan output | `m6-trivy-scan-backend.png`, `m6-trivy-scan-frontend.png`, `m6-trivy-before-hardening-findings.png`, `m6-trivy-pipeline.png` |
| Written explanation | [security-scan.md](security-scan.md) |

## M7 — Terraform (mock AWS via moto)
| Requirement | Evidence |
|---|---|
| HCL files | `terraform/*.tf`, `terraform/terraform.tfvars.example` |
| `terraform init` | `m7-terraform-init.png` |
| `terraform plan` (25 to add) | `m7-terraform-plan.png`, `m7-terraform-plan-resources.png` |
| `terraform apply` | `m7-terraform-apply.png` |
| VPC + 2 public subnets + EKS + node group | `m7-aws-vpc-eks-mock-console.png` (AWS CLI against the mock AWS endpoint; no real AWS console exists for the mock) |
| `terraform destroy` | `m7-terraform-destroy.png` (25 destroyed, then verified empty) |

## M8 — Kubernetes + Helm
| Requirement | Evidence |
|---|---|
| Namespace + bootstrap manifests | `k8s/namespace.yaml`, `k8s/kind-config.yaml`, `k8s/traefik-values.yaml`; `m8-kubectl-apply-namespace.png` |
| Helm chart | `helm/pantrypal/` (`Chart.yaml`, `values.yaml`, `templates/`) |
| `helm upgrade --install` | `m8-helm-upgrade-install.png` |
| 2 replicas each, all Running | `m8-kubectl-get-pods.png` |
| ClusterIP services | `m8-kubectl-get-svc.png` |
| `helm list` | `m8-helm-list.png` |
| Ingress `/` → frontend, `/api` → backend | `helm/pantrypal/templates/ingress.yaml`; `m8-kubectl-get-ingress-deploy.png` |
| App through the Ingress hostname | `m8-app-via-ingress.png` (`http://pantrypal.localtest.me`) |

## M9 — Observability
| Requirement | Evidence |
|---|---|
| Helm values | `monitoring/prometheus-values.yaml`, `monitoring/grafana-values.yaml`, `monitoring/dashboards/pantrypal-api.json` |
| `/metrics` output | `m9-curl-backend-metrics.png` |
| Prometheus target UP | `m9-prometheus-targets-up.png`, `m9-prometheus-query.png` |
| Grafana dashboard with live panels | `m9-grafana-dashboard.png` |

## M10 — Documentation + demo
| Requirement | Evidence |
|---|---|
| README | `README.md` |
| Live demo script | [demo.md](demo.md) |
