#!/bin/bash

# Deploy Cloud Run application with latest Docker image
# This script forces Cloud Run to pull the latest image from Artifact Registry

set -e  # Exit on error

# Configuration
PROJECT_ID="deadlock-485121"
REGION="europe-west2"
SERVICE_NAME="deadlock-analytics"
IMAGE_URL="europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest"

echo "=========================================="
echo "Cloud Run Deployment Script"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $IMAGE_URL"
echo "=========================================="
echo ""

# Update Cloud Run service with latest image
echo "Deploying latest image to Cloud Run..."
gcloud run services update "$SERVICE_NAME" \
  --region="$REGION" \
  --image="$IMAGE_URL" \
  --project="$PROJECT_ID"

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

echo "Service URL: $SERVICE_URL"
echo ""
