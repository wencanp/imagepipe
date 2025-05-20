#!/bin/bash

# Auto deployment script: from building Docker images to deploying on Minikube

set -e

echo "[1/5] Switching Docker env to Minikube ..."
eval $(minikube docker-env)

echo "[2/5] Building backend images ..."
docker build -t imagepipe-gateway ./services/gateway
docker build -t imagepipe-worker-convert ./services/convert
docker build -t imagepipe-worker-filter ./services/filter
docker build -t imagepipe-worker-ocr ./services/ocr
docker build -t imagepipe-worker-cleaner ./services/cleaner

echo "[3/5] Building frontend images ..."
docker build -t imagepipe-frontend ./frontend

echo "[4/5] Creating/Updating secret conf ..."
kubectl delete secret imagepipe-secret --ignore-not-found
kubectl create secret generic imagepipe-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=mypassword \
  --from-literal=POSTGRES_DB=imagepipe \
  --from-literal=MINIO_ROOT_USER=minioadmin \
  --from-literal=MINIO_ROOT_PASSWORD=minioadmin \
  --from-literal=S3_ENDPOINT_URL=http://minio:9000 \
  --from-literal=MINIO_PUBLIC_HOST=192.168.49.2:31001 \
  --from-literal=REACT_APP_API_URL=http://192.168.49.2:30000

echo "[5/5] Appling Kubernetes config with YAMLs ..."
kubectl apply -f k8s/

echo "[Completed] Deployed!"
echo "    - Frontend: http://frontend.192.168.49.2.nip.io"
echo "    - MinIO: http://192.168.49.2:31002"