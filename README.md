# Real Estate Data Scraper for Suumo.jp

This project contains a web scraper to collect real estate data from [Suumo.jp](https://suumo.jp/) and store it in a MongoDB database for future analysis.

![Project Screenshot](https://github.com/Takusei/realEstate/assets/45616321/84d652c7-fbdd-4a07-b513-50af99debd5e)

## Prerequisites

Before you begin, ensure you have the following tools installed:
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Kubernetes CLI (kubectl)](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [Minikube](httpss://minikube.sigs.k8s.io/docs/start/) (for local Kubernetes deployment)

## Configuration

The application requires a `MONGO_URI` environment variable to connect to the database. The value depends on the deployment environment:

- **Local Machine:** `localhost`
- **Docker Compose:** `mongodb` (the service name) or `host.docker.internal`
- **Kubernetes:** `mongodb.realestate.svc.cluster.local`

## Running the Application

You can run the application using either Docker Compose or Kubernetes.

### 1. Using Docker Compose

This is the simplest way to get the scraper and database running.

1.  **Build and Run Services:**
    This command will build the Docker images and start the containers in detached mode. The `--volumes` flag ensures any old data is cleared.
    ```bash
    docker compose down --volumes && docker compose up --build -d
    ```

2.  **Accessing MongoDB:**
    Use the following connection string with a MongoDB client:
    ```
    mongodb://admin:password@localhost:27017/suumo?authSource=admin
    ```

### 2. Using Kubernetes (with Minikube)

Follow these steps to deploy the application to a local Kubernetes cluster.

1.  **Build the Scraper Image:**
    Build the Docker image for the scraper service locally.
    ```bash
    docker build -f ./scraper/docker/Dockerfile -t suumo-scraper:latest ./scraper/. --no-cache
    ```

2.  **Load Image into Minikube:**
    Make the local image available to your Minikube cluster.
    ```bash
    minikube image load suumo-scraper:latest
    ```

3.  **Deploy to Kubernetes:**
    Apply the deployment manifest. This file was generated from `docker-compose.yaml` using `kompose`.
    ```bash
    kubectl apply -f deployment.yaml
    ```

4.  **Verify the Deployment:**
    Check that all pods and services are running in the `realestate` namespace.
    ```bash
    kubectl -n realestate get all
    ```

5.  **Accessing MongoDB:**
    Forward the MongoDB port from the cluster to your local machine.
    ```bash
    kubectl -n realestate port-forward deployments/mongodb 27017:27017
    ```
    You can then use the same connection string as in the Docker Compose setup.

## Maintenance

Here are some useful commands for cleaning up your Docker environment.

-   **Remove all stopped containers and volumes:**
    ```bash
    docker rm -vf $(docker ps -aq)
    ```

-   **Remove all Docker images:**
    ```bash
    docker rmi -f $(docker images -aq)
    ```