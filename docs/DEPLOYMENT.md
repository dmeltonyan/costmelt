# Cost Melt - Production Deployment Guide

Complete guide for deploying Cost Melt to production environments: Railway, Render, and AWS ECS (Fargate).

---

## Table of Contents

- [Overview](#overview)
- [Common Requirements](#common-requirements)
- [Deploying to Railway](#deploying-to-railway)
- [Deploying to Render](#deploying-to-render)
- [Deploying to AWS ECS (Fargate)](#deploying-to-aws-ecs-fargate)
- [Environment Variables](#environment-variables)
- [CI/CD Recommendations](#cicd-recommendations)
- [Security & Production Tips](#security--production-tips)

---

## Overview

Cost Melt is designed to be self-hosted and fully containerized using Docker. All services can be deployed independently or together, depending on your infrastructure needs.

### Architecture

The recommended production setup consists of:

- **Backend** – FastAPI service running on a scalable container platform
- **Dashboard** – Next.js application deployed as a static site or Node.js service
- **Landing** – Next.js marketing site deployed as a static site or Node.js service
- **Redis** – Managed Redis service (or containerized for small deployments)
- **Supabase** – Managed cloud project for Postgres database and vector search

### Deployment Options

This guide covers three production-ready deployment platforms:

1. **Railway** – Simple, developer-friendly platform with Docker support
2. **Render** – Modern platform with Docker and Node.js support
3. **AWS ECS (Fargate)** – Enterprise-grade container orchestration on AWS

All three options support Docker containers and provide the necessary infrastructure for running Cost Melt in production.

---

## Common Requirements

Before deploying to any platform, ensure you have:

### Prerequisites

- **Docker images built and pushed** to a registry (Docker Hub, GitHub Container Registry, AWS ECR, etc.)
- **Supabase project** created with database schema migrated
- **API keys** for at least one LLM provider (OpenAI, Anthropic, Groq, or DeepSeek)
- **Domain name** (optional but recommended for production)

### Building Docker Images

From the repository root, build and tag all images:

```bash
# Build images
docker build -t your-docker-username/costmelt-backend:latest ./backend
docker build -t your-docker-username/costmelt-dashboard:latest ./dashboard
docker build -t your-docker-username/costmelt-landing:latest ./landing

# Push to Docker Hub
docker push your-docker-username/costmelt-backend:latest
docker push your-docker-username/costmelt-dashboard:latest
docker push your-docker-username/costmelt-landing:latest
```

### Alternative: GitHub Container Registry (GHCR)

```bash
# Tag for GHCR
docker tag costmelt-backend:latest ghcr.io/your-username/costmelt-backend:latest
docker tag costmelt-dashboard:latest ghcr.io/your-username/costmelt-dashboard:latest
docker tag costmelt-landing:latest ghcr.io/your-username/costmelt-landing:latest

# Push to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin
docker push ghcr.io/your-username/costmelt-backend:latest
docker push ghcr.io/your-username/costmelt-dashboard:latest
docker push ghcr.io/your-username/costmelt-landing:latest
```

### Database Migration

Before deploying, ensure your Supabase database schema is set up:

1. Open your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and execute the contents of `backend/db/schema.sql`
4. Verify tables are created: `requests`, `cache`, `users`, `api_keys`

---

## Deploying to Railway

Railway is a developer-friendly platform that makes deploying Docker containers simple. It supports automatic deployments from Docker Hub and GitHub.

### Setup

1. Sign up at [railway.app](https://railway.app)
2. Create a new **Project**
3. Connect your GitHub repository (optional, for auto-deploy)

### Backend on Railway

#### Step 1: Create Backend Service

1. In your Railway project, click **New Service**
2. Select **Deploy from Docker Hub**
3. Enter image name: `your-docker-username/costmelt-backend:latest`
4. Click **Deploy**

#### Step 2: Configure Environment Variables

In the service settings, add these environment variables:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROQ_API_KEY=gsk_your-groq-key
DEEPSEEK_API_KEY=sk-your-deepseek-key
REDIS_URL=redis://default:password@redis-service:6379
LOG_LEVEL=info
```

#### Step 3: Configure Port

1. Go to **Settings** → **Networking**
2. Set **Port** to `8000`
3. Railway will automatically expose the service

#### Step 4: Set Start Command (Optional)

If your Dockerfile doesn't specify a CMD, add in **Settings** → **Deploy**:

```
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Step 5: Get Public URL

Railway will provide a public URL like:
```
https://costmelt-backend-production.up.railway.app
```

This is your `BACKEND_URL` for dashboard and landing services.

### Redis on Railway

#### Option 1: Railway Redis Plugin

1. Click **New Service** → **Database** → **Add Redis**
2. Railway will create a managed Redis instance
3. Copy the connection URL from the service
4. Use this URL as `REDIS_URL` in your backend service

#### Option 2: Redis Docker Service

1. Click **New Service** → **Deploy from Docker Hub**
2. Enter image: `redis:7-alpine`
3. Add environment variable: `REDIS_PASSWORD=your-secure-password`
4. Use connection string: `redis://default:your-secure-password@redis-service:6379`

### Dashboard on Railway

1. Click **New Service** → **Deploy from Docker Hub**
2. Enter image: `your-docker-username/costmelt-dashboard:latest`
3. Add environment variable:
   ```
   NEXT_PUBLIC_BACKEND_URL=https://costmelt-backend-production.up.railway.app
   ```
4. Set **Port** to `3000` in **Settings** → **Networking**
5. Railway will provide a public URL like:
   ```
   https://costmelt-dashboard-production.up.railway.app
   ```

### Landing on Railway

1. Click **New Service** → **Deploy from Docker Hub**
2. Enter image: `your-docker-username/costmelt-landing:latest`
3. Set **Port** to `3000` in **Settings** → **Networking**
4. Railway will provide a public URL like:
   ```
   https://costmelt-landing-production.up.railway.app
   ```

### Custom Domains

Railway supports custom domains:

1. Go to **Settings** → **Networking** → **Custom Domain**
2. Add your domain (e.g., `api.costmelt.io`)
3. Follow DNS instructions to point your domain to Railway
4. Railway will automatically provision SSL certificates

---

## Deploying to Render

Render is a modern platform that supports Docker, Node.js, and static sites. It provides automatic SSL, zero-downtime deployments, and built-in monitoring.

### Setup

1. Sign up at [render.com](https://render.com)
2. Create a new **Blueprint** or deploy services individually

### Backend on Render

#### Option 1: Using render.yaml

Create a `render.yaml` file in your repository root:

```yaml
services:
  - type: web
    name: costmelt-backend
    env: docker
    plan: starter
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    autoDeploy: true
    healthCheckPath: /health
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: DEEPSEEK_API_KEY
        sync: false
      - key: REDIS_URL
        sync: false
      - key: LOG_LEVEL
        value: info
```

#### Option 2: Manual Setup

1. Go to **Dashboard** → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `costmelt-backend`
   - **Environment:** `Docker`
   - **Dockerfile Path:** `./backend/Dockerfile`
   - **Docker Context:** `./backend`
   - **Plan:** `Starter` or `Standard`
4. Add environment variables (see [Environment Variables](#environment-variables) section)
5. Click **Create Web Service**

Render will build and deploy your service. The public URL will be:
```
https://costmelt-backend.onrender.com
```

### Redis on Render

1. Go to **Dashboard** → **New** → **Redis**
2. Configure:
   - **Name:** `costmelt-redis`
   - **Plan:** `Starter` or `Standard`
3. Click **Create Redis**
4. Copy the **Internal Redis URL** from the service dashboard
5. Use this URL as `REDIS_URL` in your backend service

**Note:** For services in the same Render account, use the internal URL format:
```
redis://red-xxxxx:6379
```

### Dashboard on Render

#### Option 1: Using render.yaml

Add to your `render.yaml`:

```yaml
  - type: web
    name: costmelt-dashboard
    env: node
    plan: starter
    buildCommand: "cd dashboard && npm install && npm run build"
    startCommand: "cd dashboard && npm run start"
    envVars:
      - key: NEXT_PUBLIC_BACKEND_URL
        value: "https://costmelt-backend.onrender.com"
```

#### Option 2: Manual Setup

1. Go to **Dashboard** → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `costmelt-dashboard`
   - **Environment:** `Node`
   - **Root Directory:** `dashboard`
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm run start`
   - **Plan:** `Starter` or `Standard`
4. Add environment variable:
   ```
   NEXT_PUBLIC_BACKEND_URL=https://costmelt-backend.onrender.com
   ```
5. Click **Create Web Service**

### Landing on Render

#### Option 1: Using render.yaml

Add to your `render.yaml`:

```yaml
  - type: web
    name: costmelt-landing
    env: node
    plan: starter
    buildCommand: "cd landing && npm install && npm run build"
    startCommand: "cd landing && npm run start"
```

#### Option 2: Manual Setup

1. Go to **Dashboard** → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `costmelt-landing`
   - **Environment:** `Node`
   - **Root Directory:** `landing`
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm run start`
   - **Plan:** `Starter` or `Standard`
4. Click **Create Web Service**

### Custom Domains

Render supports custom domains with automatic SSL:

1. Go to **Settings** → **Custom Domains**
2. Add your domain (e.g., `api.costmelt.io`)
3. Follow DNS instructions to add CNAME record
4. Render will automatically provision SSL certificates

---

## Deploying to AWS ECS (Fargate)

AWS ECS (Elastic Container Service) with Fargate provides serverless container orchestration. This setup is ideal for production workloads requiring high availability, auto-scaling, and enterprise-grade infrastructure.

### Architecture Overview

The deployment consists of:

- **ECR (Elastic Container Registry)** – Docker image storage
- **ECS Fargate Services** – Container orchestration
- **Application Load Balancer (ALB)** – Traffic routing and SSL termination
- **CloudWatch** – Logging and monitoring
- **ElastiCache** (optional) – Managed Redis service

### Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Docker installed locally
- Domain name with Route 53 hosted zone (for custom domains)

### Step 1: Push Images to ECR

#### Create ECR Repositories

```bash
# Set your AWS account ID and region
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=us-east-1

# Create repositories
aws ecr create-repository --repository-name costmelt-backend --region $AWS_REGION
aws ecr create-repository --repository-name costmelt-dashboard --region $AWS_REGION
aws ecr create-repository --repository-name costmelt-landing --region $AWS_REGION
```

#### Login to ECR

```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

#### Tag and Push Images

```bash
# Backend
docker tag costmelt-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/costmelt-backend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/costmelt-backend:latest

# Dashboard
docker tag costmelt-dashboard:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/costmelt-dashboard:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/costmelt-dashboard:latest

# Landing
docker tag costmelt-landing:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/costmelt-landing:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/costmelt-landing:latest
```

### Step 2: Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name costmelt-cluster --region $AWS_REGION
```

### Step 3: Create Task Definitions

#### Backend Task Definition

Create `backend-task-definition.json`:

```json
{
  "family": "costmelt-backend-task",
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512",
  "requiresCompatibilities": ["FARGATE"],
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "costmelt-backend",
      "image": "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/costmelt-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "info"
        }
      ],
      "secrets": [
        {
          "name": "SUPABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:costmelt/supabase-url"
        },
        {
          "name": "SUPABASE_SERVICE_KEY",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:costmelt/supabase-key"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:costmelt/openai-key"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:costmelt/redis-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/costmelt-backend",
          "awslogs-region": "<REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://backend-task-definition.json --region $AWS_REGION
```

#### Dashboard Task Definition

Create `dashboard-task-definition.json`:

```json
{
  "family": "costmelt-dashboard-task",
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512",
  "requiresCompatibilities": ["FARGATE"],
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "costmelt-dashboard",
      "image": "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/costmelt-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "NEXT_PUBLIC_BACKEND_URL",
          "value": "https://api.costmelt.yourdomain.com"
        },
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/costmelt-dashboard",
          "awslogs-region": "<REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://dashboard-task-definition.json --region $AWS_REGION
```

#### Landing Task Definition

Create `landing-task-definition.json`:

```json
{
  "family": "costmelt-landing-task",
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512",
  "requiresCompatibilities": ["FARGATE"],
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "costmelt-landing",
      "image": "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/costmelt-landing:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/costmelt-landing",
          "awslogs-region": "<REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition --cli-input-json file://landing-task-definition.json --region $AWS_REGION
```

### Step 4: Create CloudWatch Log Groups

```bash
aws logs create-log-group --log-group-name /ecs/costmelt-backend --region $AWS_REGION
aws logs create-log-group --log-group-name /ecs/costmelt-dashboard --region $AWS_REGION
aws logs create-log-group --log-group-name /ecs/costmelt-landing --region $AWS_REGION
```

### Step 5: Create VPC and Networking

#### Create VPC (if needed)

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --region $AWS_REGION

# Create subnets (at least 2 for high availability)
aws ec2 create-subnet --vpc-id <VPC_ID> --cidr-block 10.0.1.0/24 --availability-zone ${AWS_REGION}a
aws ec2 create-subnet --vpc-id <VPC_ID> --cidr-block 10.0.2.0/24 --availability-zone ${AWS_REGION}b

# Create security group
aws ec2 create-security-group --group-name costmelt-sg --description "Cost Melt security group" --vpc-id <VPC_ID> --region $AWS_REGION
```

#### Security Group Rules

```bash
# Allow inbound HTTP/HTTPS from ALB
aws ec2 authorize-security-group-ingress \
  --group-id <SECURITY_GROUP_ID> \
  --protocol tcp \
  --port 8000 \
  --source-group <ALB_SECURITY_GROUP_ID> \
  --region $AWS_REGION

# Allow inbound from ALB for dashboard/landing
aws ec2 authorize-security-group-ingress \
  --group-id <SECURITY_GROUP_ID> \
  --protocol tcp \
  --port 3000 \
  --source-group <ALB_SECURITY_GROUP_ID> \
  --region $AWS_REGION
```

### Step 6: Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name costmelt-alb \
  --subnets <SUBNET_ID_1> <SUBNET_ID_2> \
  --security-groups <ALB_SECURITY_GROUP_ID> \
  --region $AWS_REGION
```

#### Create Target Groups

```bash
# Backend target group
aws elbv2 create-target-group \
  --name costmelt-backend-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id <VPC_ID> \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --region $AWS_REGION

# Dashboard target group
aws elbv2 create-target-group \
  --name costmelt-dashboard-tg \
  --protocol HTTP \
  --port 3000 \
  --vpc-id <VPC_ID> \
  --health-check-path / \
  --health-check-interval-seconds 30 \
  --region $AWS_REGION

# Landing target group
aws elbv2 create-target-group \
  --name costmelt-landing-tg \
  --protocol HTTP \
  --port 3000 \
  --vpc-id <VPC_ID> \
  --health-check-path / \
  --health-check-interval-seconds 30 \
  --region $AWS_REGION
```

#### Create Listeners

```bash
# HTTPS listener (port 443) with SSL certificate
aws elbv2 create-listener \
  --load-balancer-arn <ALB_ARN> \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=<ACM_CERTIFICATE_ARN> \
  --default-actions Type=forward,TargetGroupArn=<BACKEND_TARGET_GROUP_ARN> \
  --region $AWS_REGION
```

#### Create Listener Rules

```bash
# Backend API rule
aws elbv2 create-rule \
  --listener-arn <LISTENER_ARN> \
  --priority 100 \
  --conditions Field=host-header,Values=api.costmelt.yourdomain.com \
  --actions Type=forward,TargetGroupArn=<BACKEND_TARGET_GROUP_ARN> \
  --region $AWS_REGION

# Dashboard rule
aws elbv2 create-rule \
  --listener-arn <LISTENER_ARN> \
  --priority 200 \
  --conditions Field=host-header,Values=dashboard.costmelt.yourdomain.com \
  --actions Type=forward,TargetGroupArn=<DASHBOARD_TARGET_GROUP_ARN> \
  --region $AWS_REGION

# Landing rule
aws elbv2 create-rule \
  --listener-arn <LISTENER_ARN> \
  --priority 300 \
  --conditions Field=host-header,Values=costmelt.yourdomain.com \
  --actions Type=forward,TargetGroupArn=<LANDING_TARGET_GROUP_ARN> \
  --region $AWS_REGION
```

### Step 7: Create ECS Services

#### Backend Service

```bash
aws ecs create-service \
  --cluster costmelt-cluster \
  --service-name costmelt-backend \
  --task-definition costmelt-backend-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<SUBNET_ID_1>,<SUBNET_ID_2>],securityGroups=[<SECURITY_GROUP_ID>],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<BACKEND_TARGET_GROUP_ARN>,containerName=costmelt-backend,containerPort=8000" \
  --region $AWS_REGION
```

#### Dashboard Service

```bash
aws ecs create-service \
  --cluster costmelt-cluster \
  --service-name costmelt-dashboard \
  --task-definition costmelt-dashboard-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<SUBNET_ID_1>,<SUBNET_ID_2>],securityGroups=[<SECURITY_GROUP_ID>],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<DASHBOARD_TARGET_GROUP_ARN>,containerName=costmelt-dashboard,containerPort=3000" \
  --region $AWS_REGION
```

#### Landing Service

```bash
aws ecs create-service \
  --cluster costmelt-cluster \
  --service-name costmelt-landing \
  --task-definition costmelt-landing-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<SUBNET_ID_1>,<SUBNET_ID_2>],securityGroups=[<SECURITY_GROUP_ID>],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<LANDING_TARGET_GROUP_ARN>,containerName=costmelt-landing,containerPort=3000" \
  --region $AWS_REGION
```

### Step 8: Redis on AWS

#### Option 1: ElastiCache (Recommended for Production)

```bash
# Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id costmelt-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --vpc-security-group-ids <REDIS_SECURITY_GROUP_ID> \
  --subnet-group-name costmelt-redis-subnet-group \
  --region $AWS_REGION
```

Get the Redis endpoint and use it in your backend task definition:
```
redis://costmelt-redis.xxxxx.cache.amazonaws.com:6379/0
```

#### Option 2: Redis Container in ECS

Create a Redis task definition and service similar to the backend service, using the `redis:7-alpine` image.

### Step 9: Auto Scaling

#### Create Auto Scaling Target

```bash
# Backend auto scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/costmelt-cluster/costmelt-backend \
  --min-capacity 2 \
  --max-capacity 10 \
  --region $AWS_REGION
```

#### Create Scaling Policy

```bash
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/costmelt-cluster/costmelt-backend \
  --policy-name costmelt-backend-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }' \
  --region $AWS_REGION
```

### Step 10: DNS Configuration

Point your domains to the ALB:

1. Get ALB DNS name from AWS Console
2. Create Route 53 A record (alias) pointing to ALB:
   - `api.costmelt.yourdomain.com` → ALB
   - `dashboard.costmelt.yourdomain.com` → ALB
   - `costmelt.yourdomain.com` → ALB

---

## Environment Variables

Production environment variables for all services:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SUPABASE_URL` | Supabase project URL | Yes | `https://xyz.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes | `sbp_...` |
| `OPENAI_API_KEY` | OpenAI API key | Optional* | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional* | `sk-ant-...` |
| `GROQ_API_KEY` | Groq API key | Optional* | `gsk_...` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | Optional* | `sk-...` |
| `REDIS_URL` | Redis connection string | Yes | `redis://user:pass@host:6379/0` |
| `LOG_LEVEL` | Logging level | No | `info` (default) |
| `NEXT_PUBLIC_BACKEND_URL` | Backend URL for dashboard | Yes (dashboard) | `https://api.costmelt.io` |

\* At least one LLM provider API key is required.

### Environment Variable Best Practices

1. **Use Secrets Managers** – Store sensitive values in:
   - AWS Secrets Manager (for ECS)
   - Render Secrets (for Render)
   - Railway Variables (for Railway)

2. **Never Commit Secrets** – Use `.env.example` files and document required variables

3. **Rotate Keys Regularly** – Implement key rotation policies

4. **Use Different Keys per Environment** – Separate dev, staging, and production keys

---

## CI/CD Recommendations

Automate building, testing, and deploying Cost Melt using CI/CD pipelines.

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

env:
  DOCKER_REGISTRY: docker.io
  DOCKER_USERNAME: your-docker-username

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.DOCKER_USERNAME }}/costmelt-backend:latest
            ${{ env.DOCKER_USERNAME }}/costmelt-backend:${{ github.sha }}
      
      - name: Build and push dashboard
        uses: docker/build-push-action@v5
        with:
          context: ./dashboard
          push: true
          tags: |
            ${{ env.DOCKER_USERNAME }}/costmelt-dashboard:latest
            ${{ env.DOCKER_USERNAME }}/costmelt-dashboard:${{ github.sha }}
      
      - name: Build and push landing
        uses: docker/build-push-action@v5
        with:
          context: ./landing
          push: true
          tags: |
            ${{ env.DOCKER_USERNAME }}/costmelt-landing:latest
            ${{ env.DOCKER_USERNAME }}/costmelt-landing:${{ github.sha }}

  deploy-railway:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@v1.0.0
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: costmelt-backend
```

### Render Auto-Deploy

Render automatically deploys when you push to the connected branch. Ensure `autoDeploy: true` is set in `render.yaml`.

### AWS ECS Deployment

Update ECS services to use new task definitions:

```bash
aws ecs update-service \
  --cluster costmelt-cluster \
  --service costmelt-backend \
  --force-new-deployment \
  --region $AWS_REGION
```

Or use AWS CodePipeline for automated deployments.

---

## Security & Production Tips

### Security Best Practices

1. **Never Commit Secrets**
   - Use `.gitignore` to exclude `.env` files
   - Store secrets in platform-specific secret managers
   - Rotate API keys regularly

2. **Use Secrets Managers**
   - **AWS:** AWS Secrets Manager or Systems Manager Parameter Store
   - **Render:** Render Secrets (encrypted at rest)
   - **Railway:** Railway Variables (encrypted)

3. **Enable HTTPS**
   - Railway and Render provide automatic SSL certificates
   - AWS: Use ACM (AWS Certificate Manager) with ALB
   - Redirect HTTP to HTTPS

4. **Implement Authentication**
   - Add API key authentication before going fully public
   - Use rate limiting (60 req/min for free tier)
   - Implement user authentication for dashboard

5. **Network Security**
   - Use private subnets for ECS tasks when possible
   - Restrict security group rules to minimum required
   - Use VPC endpoints for AWS services

6. **Monitor and Log**
   - Enable CloudWatch logs (AWS)
   - Monitor Render/Railway logs
   - Set up alerts for errors and high latency
   - Track cost metrics and usage patterns

### Production Optimizations

1. **Use Managed Redis**
   - Prefer ElastiCache (AWS) or managed Redis (Render/Railway)
   - Configure Redis persistence for data durability
   - Set appropriate memory limits

2. **Enable Auto-Scaling**
   - Configure auto-scaling based on CPU/memory metrics
   - Set minimum and maximum instance counts
   - Use target tracking policies for smooth scaling

3. **Database Optimization**
   - Use Supabase connection pooling
   - Enable query performance monitoring
   - Set up database backups

4. **CDN for Static Assets**
   - Use CloudFront (AWS) or similar for dashboard/landing
   - Cache static assets aggressively
   - Enable compression

5. **Health Checks**
   - Configure health check endpoints (`/health`)
   - Set appropriate health check intervals
   - Use health checks for auto-scaling decisions

6. **Cost Optimization**
   - Use appropriate instance sizes (start small, scale up)
   - Enable spot instances for non-critical workloads (AWS)
   - Monitor and optimize Redis memory usage
   - Set up billing alerts

### Monitoring Recommendations

1. **Application Metrics**
   - Request rate and latency
   - Error rates by endpoint
   - Cache hit rates
   - Cost savings metrics

2. **Infrastructure Metrics**
   - CPU and memory utilization
   - Network throughput
   - Container health
   - Database connection pool usage

3. **Alerting**
   - High error rates (> 5%)
   - High latency (> 1s p95)
   - Service unavailability
   - Cost threshold exceeded

### Backup and Disaster Recovery

1. **Database Backups**
   - Supabase provides automatic daily backups
   - Configure point-in-time recovery if needed
   - Test restore procedures regularly

2. **Configuration Backups**
   - Version control all infrastructure as code
   - Document all environment variables
   - Keep deployment scripts in repository

3. **Disaster Recovery Plan**
   - Document recovery procedures
   - Test failover scenarios
   - Maintain runbooks for common issues

---

## Platform Comparison

| Feature | Railway | Render | AWS ECS (Fargate) |
|---------|---------|--------|-------------------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Cost (Small Scale)** | Low | Low | Medium |
| **Cost (Large Scale)** | Medium | Medium | Low (with optimization) |
| **Auto-Scaling** | ✅ | ✅ | ✅ (advanced) |
| **Custom Domains** | ✅ | ✅ | ✅ |
| **SSL Certificates** | Automatic | Automatic | Manual (ACM) |
| **Logging** | Built-in | Built-in | CloudWatch |
| **Monitoring** | Basic | Basic | Advanced |
| **VPC Support** | ❌ | ❌ | ✅ |
| **Enterprise Features** | Limited | Limited | Extensive |

### Recommendation

- **Start with Railway or Render** for quick deployment and ease of use
- **Migrate to AWS ECS** when you need:
  - Advanced networking (VPC, private subnets)
  - Enterprise compliance requirements
  - Fine-grained cost optimization
  - Integration with other AWS services

---

## Troubleshooting

### Common Issues

**Service won't start:**
- Check environment variables are set correctly
- Verify Docker image is accessible
- Review logs for startup errors

**Connection errors:**
- Verify Redis URL format
- Check security group rules (AWS)
- Ensure services can communicate

**High latency:**
- Check Redis connection
- Verify database connection pooling
- Review auto-scaling configuration

**Cost overruns:**
- Monitor usage in dashboard
- Set up billing alerts
- Review and optimize routing rules

---

## Support

For deployment assistance:

- **Documentation:** [https://docs.costmelt.com](https://docs.costmelt.com)
- **GitHub Issues:** [https://github.com/your-username/costmelt/issues](https://github.com/your-username/costmelt/issues)
- **Email:** support@costmelt.com

---

**Last Updated:** January 2025

