# 💰 YLM Salary Tracker

> **Track your salary with style!** A modern, full-stack web application for automatic salary tracking with AWS deployment.

## 🎯 Overview

YLM Salary Tracker is a production-ready web application that automatically scrapes attendance data and calculates salary information. Built with Flask backend, responsive frontend, and fully containerized for AWS EC2 deployment.

## ✨ Features

- 🔄 **Automatic Data Sync** - Scrapes attendance data from your system
- 📊 **Real-time Calculations** - Instantly calculates salary breakdown
- 🎨 **Modern UI** - Glassmorphism design with smooth animations
- 🐳 **Docker Ready** - Fully containerized for easy deployment
- ☁️ **AWS Optimized** - Terraform IaC for AWS Free Tier
- 🔒 **Secure** - Environment variables and security best practices
- 🤖 **Automated Agent** - Quality checks, monitoring, and improvements

## 🏗️ Architecture

```
salary-tracker/
├── backend/          # Flask API server
│   ├── app.py       # Main Flask application
│   ├── scraper.py   # Web scraping logic
│   ├── calculator.py # Salary calculations
│   └── config.py    # Configuration management
├── frontend/         # Static web interface
│   ├── index.html
│   ├── style.css
│   └── script.js
├── infra/           # Terraform Infrastructure as Code
│   ├── main.tf      # AWS EC2 deployment
│   └── cloudwatch_lambda.tf # Monitoring & Lambda
├── agent/           # 🤖 Automated Agent
│   ├── main_agent.py # Main quality checker
│   ├── lambda_monitor.py # AWS Lambda monitoring
│   └── deploy.sh    # Automated deployment
├── data/            # Local data storage
├── Dockerfile       # Multi-stage Docker build
└── requirements.txt # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose (optional)
- AWS CLI (for deployment)
- Terraform (for infrastructure)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/shakedr2/salary-tracker.git
cd salary-tracker
```

2. **Set up environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure credentials**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Run the application**
```bash
python backend/app.py
```

Visit `http://localhost:5000` 🎉

### 🐳 Docker Deployment

**Build and run with Docker:**
```bash
# Build image
docker build -t salary-tracker .

# Run container
docker run -p 5000:5000 \
  -e YLM_USERNAME=your_username \
  -e YLM_PASSWORD=your_password \
  salary-tracker
```

## ☁️ AWS Deployment (Free Tier)

### Step 1: Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
```

### Step 2: Generate SSH Key (if needed)

```bash
# On Windows (PowerShell)
ssh-keygen -t rsa -b 4096 -f C:/Users/YOUR_USERNAME/.ssh/id_rsa

# On Linux/Mac
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
```

### Step 3: Deploy with Terraform

```bash
cd infra

# Initialize Terraform
terraform init

# Review deployment plan
terraform plan

# Deploy infrastructure
terraform apply
```

**Note:** The infrastructure is optimized for **AWS Free Tier**:
- Instance Type: `t2.micro` (1 vCPU, 1GB RAM)
- EBS Volume: 8GB (Free Tier eligible)
- Region: `us-east-1`

### Step 4: Deploy Application

After Terraform creates your EC2 instance:

```bash
# Get your server IP
terraform output server_public_ip

# SSH into your server
ssh -i C:/Users/YOUR_USERNAME/.ssh/id_rsa ubuntu@YOUR_SERVER_IP

# On the server:
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Clone and run
git clone https://github.com/shakedr2/salary-tracker.git
cd salary-tracker
sudo docker build -t salary-tracker .
sudo docker run -d -p 80:5000 \
  -e YLM_USERNAME=your_username \
  -e YLM_PASSWORD=your_password \
  --restart unless-stopped \
  salary-tracker
```

Visit `http://YOUR_SERVER_IP` 🚀

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `YLM_USERNAME` | Your system username | Yes |
| `YLM_PASSWORD` | Your system password | Yes |
| `FLASK_HOST` | Flask server host | No (default: 0.0.0.0) |
| `FLASK_PORT` | Flask server port | No (default: 5000) |
| `FLASK_DEBUG` | Debug mode | No (default: False) |

### Terraform Variables

Edit `infra/main.tf` to customize:
- AWS Region
- Instance Type
- SSH Key Path
- Security Group Rules

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serve frontend |
| `GET` | `/api/salary` | Get salary data |
| `POST` | `/api/refresh` | Refresh data from source |
| `GET` | `/api/health` | Health check |

## 🛠️ Tech Stack

- **Backend:** Flask (Python 3.9)
- **Frontend:** Vanilla JS, CSS3, HTML5
- **Containerization:** Docker
- **Infrastructure:** Terraform, AWS EC2
- **Web Scraping:** Selenium, BeautifulSoup

## 🤖 Automated Agent

The project includes an automated agent that checks and improves the software:

### Quick Check
```bash
# Run automated quality checks
python agent/main_agent.py

# Or use the quick check script
bash agent/quick_check.sh
```

### Features
- ✅ **Code Quality Checks** - Syntax, imports, security
- ✅ **Test Execution** - Automated test runs
- ✅ **AWS Infrastructure Monitoring** - EC2, Security Groups, CloudWatch
- ✅ **Improvement Suggestions** - Automated recommendations
- ✅ **Lambda Integration** - CloudWatch-based monitoring

### Full Documentation
See [agent/README.md](agent/README.md) for complete agent documentation.

## 📊 Observability & Monitoring

### Structured Logging
The application uses structured JSON logging compatible with CloudWatch Logs:
- All logs are in JSON format
- Includes timestamps, log levels, and context
- Ready for CloudWatch Logs ingestion

### Metrics Endpoint
Access application metrics at `/api/metrics`:
```bash
curl http://localhost:5000/api/metrics
```

Returns:
- Scraping metrics (runs, success rate, duration)
- Calculation metrics (days processed, total salary)
- API metrics (requests, errors)
- Health metrics (uptime, status)

### CloudWatch Dashboard
After deploying to AWS, set up a CloudWatch Dashboard:

1. **Go to CloudWatch Console** → Dashboards → Create Dashboard
2. **Add widgets for:**
   - EC2 CPU Utilization
   - Application Health (from `/api/health`)
   - Scraping Success Rate
   - API Request Count
   - Error Rate

3. **Use Lambda Monitor** (from `agent/lambda_monitor.py`) to push custom metrics

### Monitoring Setup
```bash
# Deploy Lambda monitor
cd agent
zip lambda_monitor.zip lambda_monitor.py
# Upload to AWS Lambda via console or CLI

# Subscribe to SNS alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:salary-tracker-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## 🔐 Authentication (Optional)

The project includes basic JWT authentication for multi-user support:

### Usage
```python
from backend.auth import require_auth, generate_token, authenticate_user

# Login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = authenticate_user(data['username'], data['password'])
    if user:
        token = generate_token(user['user_id'], user['username'])
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

# Protected endpoint
@app.route('/api/protected', methods=['GET'])
@require_auth
def protected():
    return jsonify({"message": f"Hello {request.current_user['username']}"})
```

### Client Usage
```javascript
// Login
const response = await fetch('/api/login', {
  method: 'POST',
  body: JSON.stringify({username: 'demo', password: 'demo123'})
});
const {token} = await response.json();

// Use token
fetch('/api/protected', {
  headers: {'Authorization': `Bearer ${token}`}
});
```

## 🚀 CI/CD Pipeline

The project includes GitHub Actions CI/CD pipeline (`.github/workflows/ci-cd.yml`):

### Pipeline Stages
1. **Test** - Run pytest with coverage
2. **Quality** - Run automated agent checks
3. **Terraform** - Validate infrastructure (on main branch)
4. **Docker** - Build and push Docker image (on main branch)

### Setup
1. Add secrets to GitHub:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`

2. Push to trigger pipeline:
```bash
git push origin main
```

### Manual Deployment
```bash
# After CI passes, deploy manually:
cd infra
terraform apply

# Or use automated deployment:
bash agent/deploy.sh
```

## 🔐 Security

- ✅ Dependabot enabled for dependency updates
- ✅ Environment variables for sensitive data
- ✅ Security group configured (SSH + HTTP only)
- ✅ Non-root user in Docker container
- ✅ Multi-stage builds for minimal attack surface
- ✅ Automated security checks via agent

## 📝 Development

### Project Structure

```python
# backend/app.py - Main Flask application
# backend/scraper.py - Selenium-based scraper
# backend/calculator.py - Salary calculation logic
# backend/config.py - Configuration management
```

### Adding Features

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Test locally: `pytest tests/`
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature/my-feature`
6. Open Pull Request

## 🐛 Troubleshooting

### Docker Issues

```bash
# View logs
docker logs <container_id>

# Access container shell
docker exec -it <container_id> /bin/bash
```

### AWS Connection Issues

```bash
# Test SSH connection
ssh -i ~/.ssh/id_rsa ubuntu@YOUR_SERVER_IP

# Check security group allows your IP
aws ec2 describe-security-groups --group-ids sg-xxx
```

## 📜 License

This project is licensed under the MIT License.

## 👤 Author

**Shaked R**
- GitHub: [@shakedr2](https://github.com/shakedr2)

## 🙏 Acknowledgments

- Built with ❤️ for efficient salary tracking
- Optimized for AWS Free Tier
- Production-ready architecture

---

⭐ **Star this repo if you find it helpful!**
