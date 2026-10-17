# M10 — Live demo: commit → pipeline → deployment update

The goal is to show one code change travelling all the way to the running cluster. The
**build badge** in the top-right of the app shows the commit SHA the backend is running,
so you can see the update happen in the browser.

## One-time setup

1. **Local cluster running**: `scripts/setup-local-cluster.sh`
2. **Self-hosted runner** on the machine that runs the kind cluster, so the `deploy` job can reach it:
   - GitHub → repo → *Settings → Actions → Runners → New self-hosted runner* (macOS), follow the commands.
   - The runner needs `kubectl` and `helm` on `PATH`, and `kubectl config current-context` must be `kind-pantrypal`.
3. **Enable the deploy job**: *Settings → Secrets and variables → Actions → Variables* → `DEPLOY_ENABLED = true`.
4. **Let the cluster pull from GHCR**. Either:
   - make both packages public (*Packages → pantrypal-backend / pantrypal-frontend → Package settings → Change visibility*), or
   - create a pull secret and pass `--set imagePullSecrets[0].name=ghcr-pull`:
     ```bash
     kubectl -n pantrypal create secret docker-registry ghcr-pull \
       --docker-server=ghcr.io --docker-username=<github-user> --docker-password=<PAT with read:packages>
     ```

## Demo script (≈5 minutes)

```bash
# terminal 1: watch pods roll
kubectl get pods -n pantrypal -w

# terminal 2: make a visible change
sed -i '' "s/Know what's in your kitchen before it goes off./Track it. Eat it. Waste less./" frontend/src/App.jsx
git commit -am "Update PantryPal tagline on the dashboard header"
git push origin main
gh run watch            # or open the Actions tab
```

What to point out while it runs:

1. **Backend lint + pytest** and **Frontend build** run in parallel. A failing test would stop everything here.
2. **Image (backend/frontend)**: build → **Trivy** scan (table in the log and step summary) → push to GHCR as `:<commit-sha>`.
3. **Deploy**: `helm upgrade --install … --set *.image.tag=<sha>`. In terminal 1, new pods start while
   old ones terminate (`maxUnavailable: 0`, so there's no downtime).
4. Refresh <http://pantrypal.localtest.me>. The new tagline appears, and the build badge shows the new short SHA.
5. `helm history pantrypal -n pantrypal` shows the new revision. Grafana keeps showing traffic throughout the rollout.

## Fallback without a self-hosted runner

After the pipeline goes green, deploy the exact images it pushed:

```bash
SHA=$(git rev-parse HEAD)
helm upgrade --install pantrypal ./helm/pantrypal -n pantrypal \
  --set backend.image.tag=$SHA --set frontend.image.tag=$SHA --wait
```
