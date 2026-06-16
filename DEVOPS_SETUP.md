# DevOps Setup Guide

This guide walks you through setting up all the accounts, tools, and local environment needed to work on this project. Follow the steps in order.

---

## Table of Contents

1. [Accounts & Credentials](#1-accounts--credentials)
   - [Google AI Studio (Gemini API)](#step-1--create-a-google-ai-studio-account-gemini-api)
   - [Pinecone](#step-2--create-a-pinecone-account)
   - [AWS](#step-3--create-an-aws-account)
   - [IAM User](#step-4--create-an-iam-user-for-the-project)
   - [LangSmith](#step-5--create-a-langsmith-account)
2. [WSL Setup (Windows only)](#2-wsl-setup-windows-only)
3. [Project Environment Setup](#3-project-environment-setup)
   - [AWS CLI](#step-1--install-aws-cli)
   - [Terraform](#step-2--install-terraform)
   - [Docker](#step-3--install-docker-inside-wsl)
   - [Project Files](#step-5--set-up-your-project-in-wsl)

---

## 1. Accounts & Credentials

### Step 1 - Create a Google AI Studio account (Gemini API)

> **Cost:** Gemini Flash is free up to 15 requests/minute. Gemini Pro also has a free tier. You won't be charged during development if you stay within limits.

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with a Google account
3. Click **"Get API key"** in the left sidebar
4. Click **"Create API key"** → select **"Create API key in new project"**
5. Copy the key and paste it as `GEMINI_API_KEY` in your `.env`

---

### Step 2 - Create a Pinecone account

> **Cost:** Free tier gives you 1 index and 2GB storage - enough for development.

1. Go to [pinecone.io](https://pinecone.io) and sign up for free
2. After login, go to **API Keys** in the left sidebar
3. Copy the default API key → paste as `PINECONE_API_KEY` in your `.env`
4. Go to **Indexes** → **Create Index** with the following settings:

| Setting    | Value         |
| ---------- | ------------- |
| Name       | `aegis-index` |
| Dimensions | `768`         |
| Metric     | `cosine`      |
| Cloud      | AWS           |
| Region     | `us-east-1`   |

5. Paste `aegis-index` as `PINECONE_INDEX_NAME` in your `.env`

---

### Step 3 - Create an AWS account

> **Cost:** You won't be charged if you stay within free tier limits.

1. Go to [aws.amazon.com](https://aws.amazon.com) → **Create an AWS Account**
2. Enter your email and choose a root account password
3. Select **"Personal"** account type
4. Enter payment details (free tier only - no charges expected)
5. Choose the **Basic (free) support plan**
6. Verify your phone number
7. Sign in to the AWS Console at [console.aws.amazon.com](https://console.aws.amazon.com)

**After signing in, complete these two security steps immediately:**

#### Enable MFA on your root account

1. Click your account name (top right) → **Security credentials**
2. Under **Multi-factor authentication** → **Assign MFA device**
3. Use an authenticator app (Google Authenticator or Authy)

> ⚠️ **Never use root credentials in code.** Root has unlimited access. Create a separate IAM user for the project instead (see next step).

---

### Step 4 - Create an IAM user for the project

1. In the AWS Console search bar, type **IAM** and open it
2. Click **Users** → **Create user**
3. Set username to `aegis-dev`
4. Do **not** check "Provide user access to the AWS Management Console" - we only need programmatic access
5. Click **Next** → **Attach policies directly**
6. Search and attach these policies:
   - `AmazonS3FullAccess`
   - `AmazonECS_FullAccess`
   - `AmazonEC2FullAccess`
   - `AmazonEC2ContainerRegistryFullAccess`
   - `CloudWatchLogsFullAccess`
   - `IAMFullAccess`
7. Click **Create user**
8. Open the user → **Security credentials** tab → **Create access key**
9. Select **"Application running outside AWS"**
10. Copy both values into your `.env`:
    - Access key ID → `AWS_ACCESS_KEY_ID`
    - Secret access key → `AWS_SECRET_ACCESS_KEY`

> ⚠️ The secret access key is shown **only once**. Copy it immediately.

---

### Step 5 - Create a LangSmith account

> **Cost:** Free tier includes 5,000 traces/month - plenty for development.

1. Go to [smith.langchain.com](https://smith.langchain.com) and sign up for free
2. After login, go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Copy it → paste as `LANGCHAIN_API_KEY` in your `.env`

---

## 2. WSL Setup (Windows only)

> Skip this section if you're on macOS or Linux, or if you already have WSL installed.

### Method 1: One-Command Install (Recommended)

Open **PowerShell** or **Command Prompt as Administrator** and run:

```powershell
wsl --install
```

This automatically installs WSL 2 + Ubuntu. **Restart your PC** when prompted. After restart, Ubuntu will launch and ask you to create a username and password.

---

### Method 2: Manual Setup

Use this if Method 1 doesn't work.

**1. Enable WSL & Virtual Machine features:**

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**2. Restart your PC**

**3. Set WSL 2 as default:**

```powershell
wsl --set-default-version 2
```

**4. Install Ubuntu:**

```powershell
wsl --install -d Ubuntu
```

---

### Verify your Ubuntu version

Open the WSL terminal (search "Ubuntu" or "WSL" in Start menu) and run:

```bash
lsb_release -a
```

You should see Ubuntu 22.04 or 24.04 - either is fine.

### Update Ubuntu and install base tools

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

```bash
sudo apt install git curl unzip -y
```

This installs:

- **git** - version control
- **curl** - download things from the web
- **unzip** - extract zip files

---

## 3. Project Environment Setup

Run all of the following commands inside your **WSL/Ubuntu terminal**.

### Step 1 - Install AWS CLI

```bash
# Download the installer
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Install unzip if you don't have it
sudo apt-get install unzip -y

# Unzip and install
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
```

You should see something like `aws-cli/2.x.x`.

**Configure with your IAM credentials from Step 4:**

```bash
aws configure
```

It will ask four things:

```
AWS Access Key ID:     <paste your AKIA... key>
AWS Secret Access Key: <paste your secret key>
Default region name:   us-east-1
Default output format: json
```

**Verify it works:**

```bash
aws sts get-caller-identity
```

You should see your AWS account ID and the IAM username `aegis-dev`. If you see this, AWS CLI is working correctly.

---

### Step 2 - Install Terraform

```bash
# Install via tfenv (version manager - recommended)
git clone https://github.com/tfutils/tfenv.git ~/.tfenv
echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Install and use Terraform 1.8.0
tfenv install 1.8.0
tfenv use 1.8.0

# Verify
terraform --version
```

---

### Step 3 - Install Docker inside WSL

> **Note:** Do not install Docker Desktop. Install Docker Engine directly inside Ubuntu.

```bash
# Remove any old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# Add Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repo
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add your user to the docker group (so you don't need sudo every time)
sudo usermod -aG docker $USER

# Start Docker service
sudo service docker start
```

**Close your WSL terminal completely and reopen it**, then verify:

```bash
docker --version
docker compose version
```

---

### Step 4 - Set up your project in WSL

> **Important:** Keep your project files inside WSL's filesystem (`/home/yourname/`), not on your Windows C: drive. This is faster and avoids permission issues.

```bash
# Go to your home directory
cd ~

# Create a projects folder
mkdir projects && cd projects

# Install git if you don't have it
sudo apt-get install -y git

# Clone the repo
git clone https://github.com/daveshenal/aegis.git
cd aegis
```

Get your account ID

```bash
aws sts get-caller-identity
```

Replace with your account ID

```bash
aws s3api create-bucket \
  --bucket aegis-tfstate-<AWS-account-ID> \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket aegis-tfstate-<AWS-account-ID> \
  --versioning-configuration Status=Enabled

```

```bash
cd infra

# Downloads the AWS provider plugin and connects to the S3 backend we created
terraform init

# Previews what AWS resources will be created without actually creating anything
terraform plan

# Ready to create everything. Run
terraform apply
```

It will show the same plan and ask you to type yes to confirm. Type yes

Store the ECR URL

```bash
export ECR_URL="<AWS-account-ID>.dkr.ecr.us-east-1.amazonaws.com/aegis"
```

Go back to your project root and start Docker:

```bash
cd ~/projects/aegis
sudo service docker start
```

Now authenticate Docker to ECR — this lets Docker push images to your AWS container registry:

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <AWS-account-ID>.dkr.ecr.us-east-1.amazonaws.com
```

You should see: Login Succeeded

Now build the image. This reads your Dockerfile and packages the entire application into a Docker image. This will take a few minutes — it's downloading the base Python image and installing all dependencies from requirements.txt

```bash
docker build -t aegis .
```

Now tag the image with the ECR URL and push it:

```bash
docker tag aegis:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

This will take a few minutes — it's uploading all the image layers to ECR
