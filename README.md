# Introduction
This repo is for crawl data from some suumo pages, and save it into `mongodb` for future use.

# Deploy
## How to run this in docker?
```
docker compose down --volumes && docker compose up --build -d
```

## How to run this in k8s?
Before run this command below, please make sure the necessary is already built in local
```
# Build the image in local
docker build -f ./scraper/docker/Dockerfile -t suumo-scraper:latest ./scraper/. --no-cache

# Load image to minikube if you are using it
minikube load suumo-scraper

# The deployment file is created from docker-compose.yaml by `kompose`
kubectl apply -f deployment.yaml
```

# Tips
```
# Remove all build volumes and containers
docker rm -vf $(docker ps -aq)

# Remove all built images
docker rmi -f $(docker images -aq)
```