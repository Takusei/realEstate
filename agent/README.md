# 🏠 Real Estate Recommendation Agent

This is a Streamlit-based web application that serves as an intelligent real estate recommendation agent. It allows users to search for properties using both structured filters and natural language queries. The agent leverages Google's Vertex AI for understanding queries and MongoDB Atlas Vector Search to find similar properties.



![Demo](./demo.png)

---

## ✨ Features

-   **Natural Language Search**: Users can type queries like "a pet-friendly apartment near Shinagawa station" to get relevant results.
-   **Hybrid Filtering**: Combine natural language queries with structured filters (e.g., budget, area, number of rooms).
-   **Similar Item Search**: Find properties similar to a selected one using:
    -   **Vector Search**: Utilizes MongoDB Atlas Vector Search for semantic similarity based on property descriptions and features.
    -   **TF-IDF**: A fallback mechanism for text-based similarity.
-   **Rate Limiting**: Implements session-based rate limiting for expensive AI model calls.
-   **Containerized Deployment**: Ready for deployment on Google Cloud Run with Docker.

---

## 🛠️ Tech Stack

-   **Frontend**: [Streamlit](https://streamlit.io/)
-   **Backend**: Python 3.12
-   **Package Management**: [uv](https://github.com/astral-sh/uv)
-   **Database**: [MongoDB Atlas](https://www.mongodb.com/atlas) (with Vector Search)
-   **AI / Embeddings**: [Google Vertex AI](https://cloud.google.com/vertex-ai)
-   **Deployment**: [Docker](https://www.docker.com/) & [Google Cloud Run](https://cloud.google.com/run)

---

## 🚀 Getting Started

### Prerequisites

-   Python 3.12
-   `uv` installed (`pip install uv`)
-   Access to a MongoDB Atlas cluster (M10 or higher for Vector Search).
-   A Google Cloud Project with Vertex AI enabled.

### 1. Set Up Environment Variables

Create a `.env` file in the `agent/` directory by copying the example below. Fill in your actual credentials and configuration.

```env
# .env file
# MongoDB Configuration
MONGO_URI="mongodb+srv://user:password@your-cluster.mongodb.net/?..."
DB_NAME="suumo"
MONGO_COLLECTION_NAME="suumo"

# Google Cloud Configuration
PROJECT_ID="your-gcp-project-id"

# Application PIN for login (optional)
APP_PIN="your-secret-pin"
```

### 2. Install Dependencies

Use `uv` to install the required Python packages from the lock file. This ensures a consistent and fast setup.

```bash
uv sync
```

---

## 🏃 Running Locally

To run the Streamlit application on your local machine, use the following command. `uv` will automatically load the variables from your `.env` file.

```bash
uv run --env-file .env streamlit run app_streamlit.py
```

The application should now be accessible at `http://localhost:8501`.

---

## ☁️ Deployment to Google Cloud Run

This application is configured for easy deployment to Google Cloud Run.

### 1. Build and Push the Docker Image

First, build the Docker image and push it to Google Container Registry (GCR) or Artifact Registry.

```bash
# Set your GCP Project ID and Image Name
export PROJECT_ID="your-gcp-project-id"
export REGION="asia-northeast1" # e.g., us-central1
export IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/rec-repo/rec-demo:latest"

# Build the image
docker build -t $IMAGE_NAME .

# Push the image
docker push $IMAGE_NAME
```

### 2. Deploy to Cloud Run

Deploy the container image using the `gcloud` CLI. This command sets the required environment variables and secrets.

**Note**: This assumes you have already configured `MONGO_URI` and `APP_PIN` as secrets in Google Secret Manager.

```bash
gcloud run deploy rec-demo \
  --image $IMAGE_NAME \
  --region $REGION \
  --allow-unauthenticated \
  --service-account your-service-account@developer.gserviceaccount.com \
  --set-secrets MONGO_URI=MONGO_URI:latest,APP_PIN=APP_PIN:latest \
  --set-env-vars DB_NAME=suumo,MONGO_COLLECTION_NAME=suumo,PROJECT_ID=$PROJECT_ID
```