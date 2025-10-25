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