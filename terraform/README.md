# Terraform Configuration for Deadlock Analytics

This directory contains Terraform configuration to deploy Deadlock Analytics to Google Cloud Run.

## Prerequisites

1. **Install Terraform**
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
   unzip terraform_1.7.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **Authenticate with GCP**
   ```bash
   gcloud auth application-default login
   ```

3. **Build and Push Docker Image**
   ```bash
   # From project root
   docker build -t flask_deadlock_analytics_app:latest .

   # Tag for Artifact Registry
   docker tag flask_deadlock_analytics_app:latest \
     europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest

   # Configure Docker auth
   gcloud auth configure-docker europe-west2-docker.pkg.dev

   # Push to Artifact Registry
   docker push europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest
   ```

## Configuration

The configuration is pre-configured with your project settings:

- **Project ID**: `deadlock-485121`
- **Region**: `europe-west2`
- **Service Account**: `sa-deadlock-cloud-run@deadlock-485121.iam.gserviceaccount.com`
- **Container Image**: `europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:latest`

You can override these values by:

1. **Editing `variables.tf`** to change defaults
2. **Using `-var` flag**:
   ```bash
   terraform apply -var="max_instances=20"
   ```
3. **Creating `terraform.tfvars`**:
   ```hcl
   max_instances = 20
   memory        = "4Gi"
   ```

## Deployment

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

This downloads the Google Cloud provider and initializes the working directory.

### 2. Review the Plan

```bash
terraform plan
```

This shows what resources will be created without actually creating them.

### 3. Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm. This will:
- Create the Cloud Run service
- Configure the service with your settings
- Enable public access (unauthenticated)

### 4. Get the Service URL

After successful deployment:
```bash
terraform output service_url
```

Or view all outputs:
```bash
terraform output
```

## Managing the Deployment

### View Current State

```bash
terraform show
```

### Update the Service

1. Modify variables in `variables.tf` or `terraform.tfvars`
2. Run:
   ```bash
   terraform plan   # Review changes
   terraform apply  # Apply changes
   ```

### Deploy a New Image Version

1. Build and push new image with a tag:
   ```bash
   docker tag flask_deadlock_analytics_app:latest \
     europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:v2
   docker push europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:v2
   ```

2. Update `variables.tf` or use a variable:
   ```bash
   terraform apply -var='container_image=europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo/flask_deadlock_analytics_app:v2'
   ```

### Destroy the Service

```bash
terraform destroy
```

Type `yes` to confirm. This removes all Terraform-managed resources.

## Configuration Options

### Memory and CPU

Adjust in `variables.tf`:
```hcl
memory = "4Gi"  # Options: 512Mi, 1Gi, 2Gi, 4Gi, 8Gi
cpu    = "4"    # Options: 1, 2, 4
```

### Scaling

```hcl
min_instances = 1   # Keep 1 instance always warm (costs more but faster cold starts)
max_instances = 20  # Maximum concurrent instances
```

### Timeout

```hcl
timeout = 300  # Maximum request timeout (seconds)
```

## Terraform State

Terraform stores state locally in `terraform.tfstate`. For production:

### Use Remote State (Recommended)

Create `backend.tf`:
```hcl
terraform {
  backend "gcs" {
    bucket = "deadlock-485121-terraform-state"
    prefix = "cloud-run/deadlock-analytics"
  }
}
```

Then:
```bash
# Create bucket first
gsutil mb gs://deadlock-485121-terraform-state

# Enable versioning
gsutil versioning set on gs://deadlock-485121-terraform-state

# Re-initialize to migrate state
terraform init -migrate-state
```

## Troubleshooting

### Permission Errors

Ensure the service account has these roles:
```bash
gcloud projects add-iam-policy-binding deadlock-485121 \
  --member="serviceAccount:sa-deadlock-cloud-run@deadlock-485121.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Image Not Found

Verify the image exists:
```bash
gcloud artifacts docker images list \
  europe-west2-docker.pkg.dev/deadlock-485121/deadlock-repo
```

### Service Won't Start

Check Cloud Run logs:
```bash
gcloud run services logs read deadlock-analytics \
  --region=europe-west2 \
  --limit=50
```

## Additional Resources

- Update the service with new environment variables
- Add custom domains
- Configure VPC connectors
- Set up Cloud SQL connections
- Add secrets from Secret Manager

Example with environment variables in `main.tf`:
```hcl
env {
  name  = "ENVIRONMENT"
  value = "production"
}

env {
  name = "DATABASE_URL"
  value_source {
    secret_key_ref {
      secret  = "database-url"
      version = "latest"
    }
  }
}
```

## CI/CD Integration

### GitHub Actions Example

`.github/workflows/deploy.yml`:
```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: hashicorp/setup-terraform@v2

      - uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Terraform Init
        run: terraform init
        working-directory: terraform

      - name: Terraform Apply
        run: terraform apply -auto-approve
        working-directory: terraform
```

## Cost Estimation

Estimate monthly costs:
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests

Calculator: https://cloud.google.com/products/calculator

With default settings (2 CPU, 2Gi RAM, scale to zero):
- Low traffic (~1000 requests/day): ~$5-10/month
- Medium traffic (~10000 requests/day): ~$20-40/month
- High traffic (~100000 requests/day): ~$150-300/month

## Version

Terraform configuration version: 1.0
Google provider version: ~> 5.0
