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