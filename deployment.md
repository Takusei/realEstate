# Deployment Guide: Scraper to Cloud Run

This guide provides the complete, step-by-step process for deploying the `suumo-scraper` application to Google Cloud Run as a scheduled job, using MongoDB Atlas as the database.

## Prerequisites

1.  **Google Cloud Account**: A project created with billing enabled.
2.  **MongoDB Atlas Cluster**: An active cluster (the free M0 tier is sufficient).
3.  **gcloud CLI**: The [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and initialized.
4.  **Docker**: Installed and running on your local machine.

---

### Step 1: Configure MongoDB Atlas

1.  **Create a Database User**: In your Atlas cluster, go to `Database Access` and create a user (e.g., `admin`) with a secure password. Grant it the `Read and write to any database` role.
2.  **Whitelist IPs**: Go to `Network Access`. For this guide, click `Add IP Address` and select `Allow Access from Anywhere` (`0.0.0.0/0`). This is required for Cloud Run to connect.
3.  **Get Connection String**: Go to `Database` -> `Connect` -> `Drivers`. Copy the connection string and replace `<password>` with the password you just created.

---

### Step 2: Configure Local GCP Environment

Run these commands in your terminal to set up your project variables and enable the required services.

```bash
# 1. Set your project ID and region
export PROJECT_ID="your-gcp-project-id" # <-- Replace with your GCP Project ID
export REGION="asia-northeast1"
gcloud config set project $PROJECT_ID

# 2. Enable the necessary APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com

# 3. Create a Docker repository in Artifact Registry
gcloud artifacts repositories create realestate-repo \
  --repository-format=docker \
  --location=$REGION
```

---

### Step 3: Store Configuration in Secret Manager

Securely store your application's environment variables in GCP Secret Manager.

```bash
# 1. Store your MongoDB Atlas connection string (replace with your actual URI)
gcloud secrets create MONGO_URI --replication-policy="automatic" --data-file=- <<EOF
mongodb+srv://admin:YOUR_ATLAS_PASSWORD@your-atlas-cluster.mongodb.net/?retryWrites=true&w=majority
EOF

# 2. Store the rest of your environment variables
gcloud secrets create MONGO_DB_NAME --replication-policy="automatic" --data-file=- <<< "suumo"
gcloud secrets create MONGO_COLLECTION_NAME --replication-policy="automatic" --data-file=- <<< "suumo"
gcloud secrets create START_PATH --replication-policy="automatic" --data-file=- <<< "https://suumo.jp/jj/common/ichiran/JJ901FC004/?initFlg=1&seniFlg=1&pc=30&ar=030&ra=030013&rnTmp=0215&kb=0&xb=0&newflg=0&km=1&rn=0215&bs=010&bs=011&bs=020"
gcloud secrets create BASE_PATH --replication-policy="automatic" --data-file=- <<< "https://suumo.jp"
```

---

### Step 4: Build and Push the Docker Image

Build the Docker image for the correct (`amd64`) architecture and push it to Artifact Registry.

```bash
# 1. Authenticate Docker with Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# 2. Define the full image name
export IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/realestate-repo/suumo-scraper:latest"

# 3. Build the image for the correct platform (amd64 for Cloud Run)
#    Run this from the root of your 'realEstate' project
docker build --platform linux/amd64 -t suumo-scraper:local -f scraper/docker/Dockerfile ./scraper

# 4. Tag the local image with the full Artifact Registry name
docker tag suumo-scraper:local $IMAGE_NAME

# 5. Push the tagged image to Artifact Registry
docker push $IMAGE_NAME
```

---

### Step 5: Grant Permissions to the Service Account

Allow the Cloud Run service account to access the secrets you created.

```bash
# Get your project number
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant the Secret Accessor role to the default compute service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

### Step 6: Create the Cloud Run Job

Deploy your container image as a Cloud Run Job, connecting the secrets as environment variables.

```bash
gcloud run jobs create suumo-scraper-job \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --task-timeout=15m \
  --set-secrets="\
MONGO_URI=MONGO_URI:latest,\
MONGO_DB_NAME=MONGO_DB_NAME:latest,\
MONGO_COLLECTION_NAME=MONGO_COLLECTION_NAME:latest,\
START_PATH=START_PATH:latest,\
BASE_PATH=BASE_PATH:latest"
```

---

### Step 7: Schedule the Job with Cloud Scheduler

Create a scheduler to trigger the job automatically. This example runs daily at 11 PM.

```bash
gcloud scheduler jobs create http run-suumo-scraper \
  --schedule="00 23 * * *" \
  --location=$REGION \
  --http-method=POST \
  --uri="https://run.googleapis.com/v1/projects/$PROJECT_ID/locations/$REGION/jobs/suumo-scraper-job:run" \
  --oauth-service-account-email="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform"
```

### Deployment Complete!

*   **To test it**, go to the Cloud Run section in the GCP Console, find `suumo-scraper-job`, and click **"EXECUTE"**.
*   **To see logs**, click on the job and view the logs for each execution.