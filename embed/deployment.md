# Automated Cloud Run deployment

After completing the [shared platform rollout](https://github.com/Takusei/gcp-platform/blob/main/docs/ROLLOUT.md), use GitHub **Actions → Deploy suumo-embed-job → Run workflow → main → Run workflow** to deploy **`suumo-embed-job`** through
[`.github/workflows/deploy-suumo-embed-job.yml`](../.github/workflows/deploy-suumo-embed-job.yml).
The shared workflow builds `linux/amd64`, publishes a commit-tagged image to
Artifact Registry, and updates the existing job using its image digest.
Runtime environment, secret bindings, service identity, and schedules are retained.
Deployment does not execute this job.

Required Actions secrets: `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT`.
Publish `Takusei/gcp-platform@main` and configure WIF **before running this workflow**.
Deployment runs only on manual dispatch from `main`; pushing code does not deploy it.

## Previous manual setup instructions

These are retained for reference; use the shared workflow for regular releases.

```
export REGION="asia-northeast1"
export PROJECT_ID="dev-projects-476011"

gcloud artifacts repositories create rec-embed \
  --repository-format=docker --location=asia-northeast1

export IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/rec-embed/suumo-embed:latest"

docker build --platform linux/amd64 -t suumo-embed:local -f embed/Dockerfile ./embed
docker tag suumo-embed:local $IMAGE_NAME
docker push $IMAGE_NAME


gcloud run jobs create suumo-embed-job \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --task-timeout=15m \
  --set-secrets="\
MONGO_URI=MONGO_URI:latest,\
DB_NAME=MONGO_DB_NAME:latest,\
MONGO_COLLECTION_NAME=MONGO_COLLECTION_NAME:latest,\
PROJECT_ID=PROJECT_ID:latest,\
APP_PIN=APP_PIN:latest"
```