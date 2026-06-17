# Aegis - DevOps Setup Guide

This guide covers the infrastructure side of Aegis. As a DevOps engineer on this project, you receive the application code from the developer and are responsible for provisioning AWS infrastructure, writing Terraform, containerising the app, and setting up CI/CD.

> **Note:** The developer has already handled Gemini, Pinecone, and LangSmith API keys. Your work starts at AWS.

---

## Table of Contents

1. [AWS Account](#step-1--create-an-aws-account)
2. [IAM User](#step-2--create-an-iam-user)
3. [WSL Setup (Windows only)](#step-3--wsl-setup-windows-only)
4. [AWS CLI](#step-4--install-aws-cli)
5. [Terraform](#step-5--install-terraform)
6. [Docker](#step-6--install-docker-inside-wsl)
7. [Project Files](#step-7--set-up-project-files)
8. [Write & Apply Terraform](#step-8--write-and-apply-terraform)
9. [Build & Push Docker Image](#step-9--build-and-push-the-docker-image)
10. [Deploy and Verify on ECS](#step-10--deploy-and-verify-on-ecs)
11. [CI/CD with GitHub Actions](#step-11--cicd-with-github-actions)
12. [Tear Down Infrastructure](#step-12--tear-down-infrastructure)

---

## Step 1 - Create an AWS Account

> **Cost:** You won't be charged if you stay within free tier limits.

1. Go to [aws.amazon.com](https://aws.amazon.com) → **Create an AWS Account**
2. Enter your email and choose a root account password
3. Select **Personal** account type
4. Enter payment details (free tier only - no charges expected)
5. Choose the **Basic (free) support plan**
6. Verify your phone number
7. Sign in to the AWS Console at [console.aws.amazon.com](https://console.aws.amazon.com)

### Enable MFA on Your Root Account

> ⚠️ Do this immediately after account creation.

1. Click your account name (top right) → **Security credentials**
2. Under **Multi-factor authentication** → **Assign MFA device**
3. Use an authenticator app (Google Authenticator or Authy)

> ⚠️ **Never use root credentials in code or Terraform.** Root has unlimited access. Create a separate IAM user instead (see Step 2).

---

## Step 2 - Create an IAM User

This IAM user (`aegis-dev`) is what your local AWS CLI, Terraform, and CI/CD pipeline will authenticate as.

1. In the AWS Console search bar, type **IAM** and open it
2. Click **Users** → **Create user**
3. Set username to `aegis-dev`
4. Do **not** check "Provide user access to the AWS Management Console" - we only need programmatic access
5. Click **Next** → **Attach policies directly**
6. Search and attach the following policies:

| Policy                                 | Purpose                                            |
| -------------------------------------- | -------------------------------------------------- |
| `AmazonS3FullAccess`                   | Terraform state bucket and app artefacts           |
| `AmazonECS_FullAccess`                 | ECS cluster, services, and tasks                   |
| `AmazonEC2FullAccess`                  | EC2 networking and load balancers                  |
| `AmazonEC2ContainerRegistryFullAccess` | Push and pull Docker images to ECR                 |
| `CloudWatchLogsFullAccess`             | Write and read application logs                    |
| `IAMFullAccess`                        | Allow Terraform to create ECS task execution roles |
| `AmazonSSMFullAccess`                  | Read secrets from SSM Parameter Store              |

7. Click **Create user**
8. Open the user → **Security credentials** tab → **Create access key**
9. Select **Application running outside AWS**
10. Copy both values - you'll need them when configuring the AWS CLI and GitHub Actions secrets

> ⚠️ The secret access key is shown **only once**. Copy it immediately and store it securely.

---

## Step 3 - WSL Setup (Windows Only)

> Skip this section if you're on macOS or Linux, or if WSL is already installed.

### Method 1: One-Command Install (Recommended)

Open **PowerShell** or **Command Prompt as Administrator** and run:

```powershell
wsl --install
```

This automatically installs WSL 2 + Ubuntu. **Restart your PC** when prompted. After restart, Ubuntu will launch and ask you to create a username and password.

### Method 2: Manual Setup

Use this if Method 1 doesn't work.

```powershell
# Enable WSL and Virtual Machine features
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

Restart your PC, then:

```powershell
wsl --set-default-version 2
wsl --install -d Ubuntu
```

### Verify and Update Ubuntu

```bash
lsb_release -a          # Should show Ubuntu 22.04 or 24.04
sudo apt-get update && sudo apt-get upgrade -y
sudo apt install git curl unzip -y
```

---

## Step 4 - Install AWS CLI

Run all of the following inside your **WSL/Ubuntu terminal**:

```bash
# Download and install
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt-get install unzip -y
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
```

Configure with your IAM credentials from Step 2:

```bash
aws configure
```

```
AWS Access Key ID:     <paste your AKIA... key>
AWS Secret Access Key: <paste your secret key>
Default region name:   us-east-1
Default output format: json
```

Verify it works:

```bash
aws sts get-caller-identity
```

You should see your AWS account ID and the IAM username `aegis-dev`.

---

## Step 5 - Install Terraform

We use `tfenv` to manage Terraform versions:

```bash
git clone https://github.com/tfutils/tfenv.git ~/.tfenv
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

tfenv install 1.8.0
tfenv use 1.8.0

terraform --version
```

---

## Step 6 - Install Docker Inside WSL

> **Note:** Do not install Docker Desktop. Install Docker Engine directly inside Ubuntu.

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies and add Docker repo
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to the docker group
sudo usermod -aG docker $USER

# Start Docker
sudo service docker start
```

**Close and reopen your WSL terminal**, then verify:

```bash
docker --version
docker compose version
```

---

## Step 7 - Set Up Project Files

> **Important:** Keep your project files inside WSL's filesystem (`/home/yourname/`), not on your Windows C: drive.

```bash
cd ~
mkdir projects && cd projects
git clone -b practice https://github.com/daveshenal/aegis.git
cd aegis
```

---

## Step 8 - Write and Apply Terraform

This is the core DevOps task. You'll write the Terraform code to provision AWS infrastructure, then apply it.

### Infrastructure to Provision

Based on the project structure, your Terraform should create the following modules under `infra/`:

```
infra/
├── main.tf
├── variables.tf
├── outputs.tf
└── modules/
    ├── ecr/       # Elastic Container Registry for Docker images
    ├── ecs/       # ECS cluster, task definition, and service
    ├── s3/        # Application artefact storage
    └── iam/       # ECS task execution role and policies
```

Each module needs at minimum `main.tf` and `outputs.tf`.

### Create the Terraform State Bucket

Once your Terraform code is written, first get your account ID:

```bash
aws sts get-caller-identity
```

Then create the S3 backend bucket (replace with your actual account ID):

```bash
aws s3api create-bucket \
  --bucket aegis-tfstate-<AWS-account-ID> \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket aegis-tfstate-<AWS-account-ID> \
  --versioning-configuration Status=Enabled
```

### Initialise, Plan, and Apply

```bash
cd infra

# Downloads the AWS provider plugin and connects to the S3 backend
terraform init

# Previews what will be created - review this carefully before applying
terraform plan

# Apply when ready
terraform apply
```

Terraform will show the plan and ask you to type `yes` to confirm.

---

## Step 9 - Build and Push the Docker Image

After Terraform has created the ECR repository, build and push the application image.

Store the ECR URL (replace with your actual account ID):

```bash
export ECR_URL="<AWS-account-ID>.dkr.ecr.us-east-1.amazonaws.com/aegis"
```

Start Docker and authenticate to ECR:

```bash
cd ~/projects/aegis
sudo service docker start

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <AWS-account-ID>.dkr.ecr.us-east-1.amazonaws.com
```

You should see: `Login Succeeded`

Build the image (reads the Dockerfile and packages the full application - takes a few minutes on first run):

```bash
docker build -t aegis .
```

Tag and push to ECR:

```bash
docker tag aegis:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

The push will take a few minutes as it uploads image layers to ECR. Once complete, the image is available for ECS to pull and run.

---

## Step 10 - Deploy and Verify on ECS

### Store Secrets in SSM Parameter Store

Before triggering a deployment, store the application secrets in AWS SSM. Run these one by one, replacing the placeholder values with your real keys:

```bash
aws ssm put-parameter \
  --name "/aegis/GEMINI_API_KEY" \
  --value "your-actual-gemini-key" \
  --type SecureString \
  --region us-east-1

aws ssm put-parameter \
  --name "/aegis/PINECONE_API_KEY" \
  --value "your-actual-pinecone-key" \
  --type SecureString \
  --region us-east-1

aws ssm put-parameter \
  --name "/aegis/LANGCHAIN_API_KEY" \
  --value "your-actual-langchain-key" \
  --type SecureString \
  --region us-east-1
```

### Force a New ECS Deployment

Now tell ECS to pull the image from ECR and start a container:

```bash
aws ecs update-service \
  --cluster aegis-cluster \
  --service aegis-service \
  --force-new-deployment \
  --region us-east-1
```

Press `q` to exit the output view.

### Watch Deployment Status

```bash
aws ecs describe-services \
  --cluster aegis-cluster \
  --services aegis-service \
  --region us-east-1 \
  --query "services[0].{Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount}"
```

You want to see:

```json
{
  "Status": "ACTIVE",
  "Desired": 1,
  "Running": 1,
  "Pending": 0
}
```

It may take 1–2 minutes for `Running` to reach `1`. If it still shows `0`, wait 30 seconds and run the command again.

### Find the Public IP

Get the task ARN first:

```bash
TASK_ARN=$(aws ecs list-tasks \
  --cluster aegis-cluster \
  --service-name aegis-service \
  --region us-east-1 \
  --query "taskArns[0]" \
  --output text)

echo $TASK_ARN
```

Get the network interface ID from that task:

```bash
ENI=$(aws ecs describe-tasks \
  --cluster aegis-cluster \
  --tasks $TASK_ARN \
  --region us-east-1 \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
  --output text)

echo $ENI
```

Use that network interface ID to get the public IP:

```bash
aws ec2 describe-network-interfaces \
  --network-interface-ids $ENI \
  --region us-east-1 \
  --query "NetworkInterfaces[0].Association.PublicIp" \
  --output text
```

### Health Check

```bash
curl http://<Public IP>:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

### Test the Research Endpoint

```bash
curl -X POST http://<Public IP>:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main approaches to retrieval-augmented generation?"}' \
  --max-time 120
```

---

## Step 11 - CI/CD with GitHub Actions

The `practice` branch includes an empty `.github/workflows/` folder. Your task is to write a `deploy.yml` workflow that automates build, push to ECR, and deploy to ECS on every push to `main`.

Add the following secrets to your GitHub repository under **Settings → Secrets and variables → Actions**:

| Secret                  | Value                               |
| ----------------------- | ----------------------------------- |
| `AWS_ACCESS_KEY_ID`     | From the IAM user created in Step 2 |
| `AWS_SECRET_ACCESS_KEY` | From the IAM user created in Step 2 |
| `AWS_REGION`            | `us-east-1`                         |

Your workflow should:
1. Trigger on push to `main`
2. Authenticate to ECR
3. Build and push the Docker image
4. Force a new ECS deployment

---

## Step 12 - Tear Down Infrastructure

> ⚠️ **Do this when you are done practising** to avoid ongoing AWS charges. ECS Fargate costs ~$0.013/hour even when idle.

### Delete the ECR Images First

Terraform cannot delete an ECR repository that still contains images. Delete them manually first:

```bash
aws ecr delete-repository \
  --repository-name aegis \
  --force \
  --region us-east-1
```

### Destroy All Terraform Resources

```bash
cd ~/projects/aegis/infra
terraform destroy
```

Type `yes` when prompted. This will remove the ECS cluster, service, task definition, IAM roles, S3 bucket, security groups, and CloudWatch log group.

### What Is NOT Deleted

The following are created manually and will remain after `terraform destroy`:

- SSM parameters (`/aegis/GEMINI_API_KEY` etc) — delete manually if needed:

```bash
aws ssm delete-parameter --name "/aegis/GEMINI_API_KEY" --region us-east-1
aws ssm delete-parameter --name "/aegis/PINECONE_API_KEY" --region us-east-1
aws ssm delete-parameter --name "/aegis/PINECONE_INDEX_NAME" --region us-east-1
aws ssm delete-parameter --name "/aegis/LANGCHAIN_API_KEY" --region us-east-1
```

- Terraform state S3 bucket — delete manually if needed:

```bash
aws s3 rb s3://aegis-tfstate-<AWS-account-ID> --force
```

### Verify Everything Is Gone

```bash
aws ecs list-clusters --region us-east-1
aws ecr describe-repositories --region us-east-1
aws s3 ls
```

All three should return empty results.

---

## Environment Variable Reference

The full list of environment variables the application requires. Developer-facing ones are managed by the developer; infrastructure-related ones are your responsibility as ECS task environment variables or SSM Parameter Store entries.

| Variable                | How to Handle                              |
| ----------------------- | ------------------------------------------ |
| `GEMINI_API_KEY`        | Store in SSM Parameter Store as SecureString |
| `GEMINI_FLASH_MODEL`    | Hardcode in ECS task definition `environment` block |
| `GEMINI_PRO_MODEL`      | Hardcode in ECS task definition `environment` block |
| `PINECONE_API_KEY`      | Store in SSM Parameter Store as SecureString |
| `PINECONE_INDEX_NAME`   | Hardcode in ECS task definition `environment` block |
| `LANGCHAIN_API_KEY`     | Store in SSM Parameter Store as SecureString |
| `LANGCHAIN_TRACING_V2`  | Hardcode in ECS task definition `environment` block |
| `LANGCHAIN_PROJECT`     | Hardcode in ECS task definition `environment` block |
| `MAX_REVISIONS`         | Hardcode in ECS task definition `environment` block |
| `MLFLOW_TRACKING_URI`   | Hardcode in ECS task definition `environment` block |
| `AWS_ACCESS_KEY_ID`     | Add as GitHub Actions secret               |
| `AWS_SECRET_ACCESS_KEY` | Add as GitHub Actions secret               |
| `S3_BUCKET_NAME`        | Pass as Terraform variable                 |
| `AWS_REGION`            | Pass as Terraform variable                 |

> ⚠️ Never hardcode secrets in Terraform files or GitHub Actions YAML. Use SSM Parameter Store or GitHub Encrypted Secrets.