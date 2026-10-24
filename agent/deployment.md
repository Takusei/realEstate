# Automated Cloud Run deployment

After completing the [shared platform rollout](https://github.com/Takusei/gcp-platform/blob/main/docs/ROLLOUT.md), use GitHub **Actions → Deploy rec-demo → Run workflow → main → Run workflow** to deploy **`rec-demo`** through
[`.github/workflows/deploy-rec-demo.yml`](../.github/workflows/deploy-rec-demo.yml).
The shared workflow builds `linux/amd64`, publishes a commit-tagged image to
Artifact Registry, and updates the existing service using its image digest.
Runtime environment, secret bindings, service identity, and schedules are retained.
The new service revision must be ready and serving all traffic for verification to pass.

Required Actions secrets: `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT`.
Publish `Takusei/gcp-platform@main` and configure WIF **before running this workflow**.
Deployment runs only on manual dispatch from `main`; pushing code does not deploy it.

## Previous manual setup instructions

These are retained for reference; use the shared workflow for regular releases.

```
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/rec-agent/suumo-agent:latest"

docker build --platform linux/amd64 -t suumo-agent:local -f agent/Dockerfile ./agent
docker tag suumo-agent:local $IMAGE_NAME
docker push $IMAGE_NAME


gcloud run deploy rec-demo \
  --image $IMAGE_NAME \
  --region $REGION \
  --allow-unauthenticated \
  --service-account 828799957094-compute@developer.gserviceaccount.com \
  --set-secrets="\
MONGO_URI=MONGO_URI:latest,\
DB_NAME=MONGO_DB_NAME:latest,\
MONGO_COLLECTION_NAME=MONGO_COLLECTION_NAME:latest,\
PROJECT_ID=PROJECT_ID:latest,\
APP_PIN=APP_PIN:latest"

gcloud run services update rec-demo \
  --region asia-northeast1 \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=1 \
  --min-instances=0 \
  --concurrency=10 \
  --timeout=600

```