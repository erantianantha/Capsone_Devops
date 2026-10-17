#!/usr/bin/env bash
# One-shot local environment: kind cluster + Traefik ingress + PantryPal (Helm)
# + Prometheus + Grafana.
#
# Usage: scripts/setup-local-cluster.sh [image_tag]
#   image_tag defaults to the current Git commit SHA. Images are built locally
#   and loaded into kind with exactly the names/tags CI pushes to GHCR.
set -euo pipefail
cd "$(dirname "$0")/.."

CLUSTER=pantrypal
OWNER="${GHCR_OWNER:-erantianantha}"
TAG="${1:-$(git rev-parse HEAD)}"
REPO="ghcr.io/${OWNER}"

step() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }

step "kind cluster"
kind get clusters | grep -qx "$CLUSTER" || kind create cluster --config k8s/kind-config.yaml
kubectl config use-context "kind-${CLUSTER}"
kubectl apply -f k8s/namespace.yaml

step "Helm repositories"
helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null
helm repo update >/dev/null

step "Traefik ingress controller"
helm upgrade --install traefik traefik/traefik --version 42.0.0 \
  -n ingress -f k8s/traefik-values.yaml --wait

step "Build and load images (tag ${TAG})"
for c in backend frontend; do
  docker build --build-arg "APP_VERSION=${TAG}" -t "${REPO}/pantrypal-${c}:${TAG}" "$c"
  kind load docker-image --name "$CLUSTER" "${REPO}/pantrypal-${c}:${TAG}"
done

step "PantryPal (Helm)"
helm upgrade --install pantrypal ./helm/pantrypal -n pantrypal \
  -f helm/pantrypal/values-dev.yaml \
  --set "backend.image.repository=${REPO}/pantrypal-backend" \
  --set "frontend.image.repository=${REPO}/pantrypal-frontend" \
  --set "backend.image.tag=${TAG}" \
  --set "frontend.image.tag=${TAG}" \
  --wait --timeout 5m

step "Prometheus"
helm upgrade --install prometheus prometheus-community/prometheus --version 29.37.0 \
  -n monitoring -f monitoring/prometheus-values.yaml --wait --timeout 6m

step "Grafana"
if ! kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1; then
  pw="$(openssl rand -base64 18 | tr -d '/+=')"
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin --from-literal=admin-password="$pw"
fi
helm upgrade --install grafana grafana/grafana --version 10.5.15 -n monitoring \
  -f monitoring/grafana-values.yaml \
  --set-file 'dashboards.default.pantrypal-api.json=monitoring/dashboards/pantrypal-api.json' \
  --wait --timeout 6m

step "Done"
kubectl get pods -n pantrypal
cat <<EOF

  App:         http://pantrypal.localtest.me
  Prometheus:  http://prometheus.localtest.me/targets
  Grafana:     http://grafana.localtest.me   (user: admin)
  Grafana password:
    kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d
  Generate dashboard traffic:
    scripts/generate-traffic.sh http://pantrypal.localtest.me 300
EOF
