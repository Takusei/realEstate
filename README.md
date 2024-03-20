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
minikube image load suumo-scraper

# The deployment file is created from docker-compose.yaml by `kompose`
kubectl apply -f deployment.yaml

# Verify it has been deployed
kubectl -n realestate get all
```

## Tips
```
# Remove all build volumes and containers
docker rm -vf $(docker ps -aq)

# Remove all built images
docker rmi -f $(docker images -aq)
```
## Note
For local, docker, k8s, we have to give MONGO_URI different string to get mongodb rui:
```
local: localhost
docker: host.docker.internal or mongodb (using the service name in docker compose)
k9s: mongodb.realestate.svc.cluster.local
```

# Access
Access mongodb with `mongodb://admin:password@localhost:27017/suumo?authSource=admin`
