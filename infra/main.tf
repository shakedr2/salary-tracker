# ============================================
# Terraform Configuration for AWS Free Tier
# Optimized for t2.micro instance
# ============================================

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"  # Free Tier available
}

# ===== Variables =====
variable "ssh_key_path" {
  description = "Path to your SSH public key"
  type        = string
  default     = "~/.ssh/id_rsa.pub"  # Default path, override if needed
}

variable "my_ip" {
  description = "Your IP address for SSH access (leave empty for 0.0.0.0/0)"
  type        = string
  default     = "0.0.0.0/0"
}

# ===== 1. VPC (Virtual Private Cloud) =====
resource "aws_vpc" "main_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "salary-tracker-vpc"
  }
}

# ===== 2. Subnet =====
resource "aws_subnet" "subnet_1" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "salary-tracker-subnet-1"
  }
}

# ===== 3. Internet Gateway =====
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main_vpc.id
  
  tags = {
    Name = "salary-tracker-igw"
  }
}

# ===== 4. Route Table =====
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main_vpc.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
  
  tags = {
    Name = "salary-tracker-public-rt"
  }
}

# ===== 5. Route Table Association =====
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}

# ===== 6. Security Group =====
resource "aws_security_group" "web_sg" {
  name        = "salary-tracker-sg"
  description = "Allow HTTP and SSH traffic"
  vpc_id      = aws_vpc.main_vpc.id
  
  # HTTP access from anywhere
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # SSH access (restricted to your IP if set)
  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "salary-tracker-sg"
  }
}

# ===== 7. SSH Key Pair =====
resource "aws_key_pair" "deployer" {
  key_name   = "salary-tracker-key"
  public_key = file(pathexpand(var.ssh_key_path))
}

# ===== 8. EC2 Instance (FREE TIER: t2.micro) =====
resource "aws_instance" "web_server" {
  # Ubuntu 22.04 LTS AMI (Free Tier eligible)
  ami           = "ami-04b70fa74e45c3917"
  instance_type = "t2.micro"  # FREE TIER
  
  subnet_id                   = aws_subnet.subnet_1.id
  vpc_security_group_ids      = [aws_security_group.web_sg.id]
  associate_public_ip_address = true
  key_name                    = aws_key_pair.deployer.key_name
  
  # Free Tier EBS: 8 GB
  root_block_device {
    volume_size = 8
    volume_type = "gp2"  # General Purpose SSD
  }
  
  # User data script to set up Docker automatically
  user_data = <<-EOF
              #!/bin/bash
              set -e
              
              # Update system
              apt-get update
              apt-get upgrade -y
              
              # Install Docker
              apt-get install -y docker.io
              systemctl start docker
              systemctl enable docker
              
              # Add ubuntu user to docker group
              usermod -aG docker ubuntu
              
              # Install Docker Compose
              curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              
              # Create app directory
              mkdir -p /home/ubuntu/app
              chown ubuntu:ubuntu /home/ubuntu/app
              
              echo "Setup complete! Docker is ready." > /home/ubuntu/setup-complete.txt
              EOF
  
  tags = {
    Name = "salary-tracker-server"
  }
}

# ===== Outputs =====
output "server_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.web_server.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh -i ${pathexpand(var.ssh_key_path)} ubuntu@${aws_instance.web_server.public_ip}"
}

output "server_url" {
  description = "URL to access the application"
  value       = "http://${aws_instance.web_server.public_ip}"
}
