#!/bin/bash
# -*- coding: utf-8 -*-
# סקריפט deployment אוטומטי
# Automated Deployment Script

set -e

echo "=========================================="
echo "🚀 Salary Tracker - Automated Deployment"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

command -v terraform >/dev/null 2>&1 || { echo -e "${RED}Terraform is required but not installed.${NC}" >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }

echo -e "${GREEN}✓ All prerequisites met${NC}"

# Step 1: Run quality checks
echo -e "\n${YELLOW}[1/5] Running quality checks...${NC}"
cd "$(dirname "$0")/.."
python agent/main_agent.py || {
    echo -e "${RED}Quality checks failed. Continue anyway? (y/n)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# Step 2: Build Docker image
echo -e "\n${YELLOW}[2/5] Building Docker image...${NC}"
docker build -t salary-tracker:latest . || {
    echo -e "${RED}Docker build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Step 3: Run tests
echo -e "\n${YELLOW}[3/5] Running tests...${NC}"
python -m pytest tests/ -v || {
    echo -e "${RED}Tests failed. Continue anyway? (y/n)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# Step 4: Deploy infrastructure
echo -e "\n${YELLOW}[4/5] Deploying AWS infrastructure...${NC}"
cd infra
terraform init
terraform plan
echo -e "${YELLOW}Apply Terraform changes? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    terraform apply -auto-approve
    SERVER_IP=$(terraform output -raw server_public_ip)
    echo -e "${GREEN}✓ Infrastructure deployed${NC}"
    echo -e "${GREEN}Server IP: ${SERVER_IP}${NC}"
else
    echo -e "${YELLOW}Skipping infrastructure deployment${NC}"
    exit 0
fi

# Step 5: Deploy application
echo -e "\n${YELLOW}[5/5] Deploying application to EC2...${NC}"
if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}Server IP not found${NC}"
    exit 1
fi

echo -e "${YELLOW}SSH key path (default: ~/.ssh/id_rsa):${NC}"
read -r SSH_KEY
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

# Save Docker image
docker save salary-tracker:latest | gzip > /tmp/salary-tracker.tar.gz

# Copy to server
echo -e "${YELLOW}Copying image to server...${NC}"
scp -i "$SSH_KEY" /tmp/salary-tracker.tar.gz ubuntu@"$SERVER_IP":/tmp/

# Deploy on server
echo -e "${YELLOW}Deploying on server...${NC}"
ssh -i "$SSH_KEY" ubuntu@"$SERVER_IP" << 'ENDSSH'
    # Load Docker image
    docker load < /tmp/salary-tracker.tar.gz
    
    # Stop existing container
    docker stop salary-tracker || true
    docker rm salary-tracker || true
    
    # Run new container
    docker run -d \
        --name salary-tracker \
        -p 80:5000 \
        --restart unless-stopped \
        -e YLM_USERNAME="${YLM_USERNAME}" \
        -e YLM_PASSWORD="${YLM_PASSWORD}" \
        salary-tracker:latest
    
    # Cleanup
    rm /tmp/salary-tracker.tar.gz
    
    echo "Deployment complete!"
ENDSSH

echo -e "\n${GREEN}=========================================="
echo -e "✅ Deployment completed successfully!"
echo -e "🌐 Application URL: http://${SERVER_IP}"
echo -e "==========================================${NC}"

