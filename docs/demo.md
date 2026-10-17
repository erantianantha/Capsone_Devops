# M10 — Live demo: commit → pipeline → deployment update

The goal is to show one code change travelling all the way to the running cluster. The
**build badge** in the top-right of the app shows the commit SHA the backend is running,
so you can see the update happen in the browser.

## One-time setup

1. **Local cluster running**: `scripts/setup-local-cluster.sh`
2. **Self-hosted runner** on the machine that runs the kind cluster, so the `deploy` job can reach it.
   Register it as **ephemeral**, so it runs one job and then removes itself. That matters on a public repo:
   ```bash
   mkdir -p ~/actions-runner && cd ~/actions-runner
   curl -sL -o runner.tar.gz https://github.com/actions/runner/releases/download/v2.338.0/actions-runner-osx-arm64-2.338.0.tar.gz
   tar xzf runner.tar.gz
   TOKEN=$(gh api -X POST repos/erantianantha/Capsone_Devops/actions/runners/registration-token --jq .token)
   ./config.sh --unattended --ephemeral --url https://github.com/erantianantha/Capsone_Devops --token "$TOKEN" --name demo-mac
   ./run.sh          # leave running; it exits after the deploy job
   ```
   The runner needs `kubectl` and `helm` on `PATH`, and `kubectl config current-context` must be `kind-pantrypal`.
3. **Enable the deploy job**: `gh variable set DEPLOY_ENABLED -b true` (or *Settings → Secrets and variables → Actions → Variables*).
   Afterwards, `gh variable delete DEPLOY_ENABLED`, so later pushes don't wait for a runner that isn't there.
4. **GHCR access**: nothing to do. Both packages (`pantrypal-backend`, `pantrypal-frontend`) are public, so
   the cluster pulls `ghcr.io/erantianantha/pantrypal-*:<sha>` without a pull secret.

## Demo script (≈5 minutes)

```bash
# terminal 1: watch pods roll
kubectl get pods -n pantrypal -w

# terminal 2: make a visible change
sed -i '' "s/Track it. Eat it. Waste less./Fresh food, less waste./" frontend/src/App.jsx   # any visible change
git commit -am "Update PantryPal tagline on the dashboard header"
git push origin main
gh run watch            # or open the Actions tab
```

What to point out while it runs:

1. **Backend lint + pytest** and **Frontend build** run in parallel. A failing test would stop everything here.
2. **Image (backend/frontend)**: build → **Trivy** scan (table in the log and step summary) → push to GHCR as `:<commit-sha>`.
3. **Deploy to kind cluster**: CI creates a fresh kind cluster, installs the chart with the new SHA and
   smoke-tests it through the Ingress. This proves the commit is deployable.
4. **Deploy to persistent cluster**: the self-hosted runner runs `helm upgrade --install … --set *.image.tag=<sha>`.
   In terminal 1, new pods start while old ones terminate (`maxUnavailable: 0`, so there's no downtime).
5. Refresh <http://pantrypal.localtest.me>. The new tagline appears, and the build badge shows the new short SHA.
6. `helm history pantrypal -n pantrypal` shows the new revision. Grafana keeps showing traffic throughout the rollout.

## Fallback without a self-hosted runner

After the pipeline goes green, deploy the exact images it pushed:

```bash
SHA=$(git rev-parse HEAD)
helm upgrade --install pantrypal ./helm/pantrypal -n pantrypal \
  --set backend.image.tag=$SHA --set frontend.image.tag=$SHA --wait
```
