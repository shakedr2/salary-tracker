terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1. יצירת הרשת הראשית (VPC)
resource "aws_vpc" "main_vpc" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "salary-tracker-vpc"
  }
}

# 2. יצירת תת-רשת ראשונה
resource "aws_subnet" "subnet_1" {
  vpc_id            = aws_vpc.main_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  
  tags = {
    Name = "salary-tracker-subnet-1"
  }
}

# 3. יצירת תת-רשת שנייה
resource "aws_subnet" "subnet_2" {
  vpc_id            = aws_vpc.main_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  
  tags = {
    Name = "salary-tracker-subnet-2"
  }
}

resource "aws_security_group" "web_sg" {
  name        = "salary-tracker-sg"
  description = "Allow HTTP and SSH traffic"
  vpc_id      = aws_vpc.main_vpc.id

  # חוק 1: מאפשר גלישה רגילה (HTTP)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # חוק 2: מאפשר התחברות לניהול (SSH) - הוספנו את זה עכשיו!
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # יציאה: הכל מותר
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

# --- החלק החדש: יצירת המפתח ב-AWS ---
resource "aws_key_pair" "deployer" {
  key_name   = "my-server-key"
  public_key = file("C:/Users/shake/.ssh/id_rsa.pub")
}

# 5. יצירת השרת
resource "aws_instance" "web_server" {
  ami           = "ami-04b70fa74e45c3917" 
  instance_type = "t3.micro"
  
  subnet_id                   = aws_subnet.subnet_1.id
  vpc_security_group_ids      = [aws_security_group.web_sg.id]
  associate_public_ip_address = true
  
  # --- חיבור המפתח לשרת ---
  key_name = aws_key_pair.deployer.key_name

  tags = {
    Name = "salary-tracker-server"
  }
}
# 7. יצירת שער לאינטרנט (Internet Gateway) - כדי שהשרת יוכל "לצאת" החוצה
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main_vpc.id

  tags = {
    Name = "salary-tracker-igw"
  }
}

# 8. יצירת טבלת ניתוב (Route Table) - "ה-Waze" של הרשת
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main_vpc.id

  # החוק אומר: כל תנועה (0.0.0.0/0) -> תשלח לשער שיצרנו למעלה
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "salary-tracker-public-rt"
  }
}

# 9. חיבור ה-Subnet שלנו לטבלת הניתוב
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}
# 6. פלט של כתובת ה-IP
output "server_public_ip" {
  description = "The public IP address of the web server"
  value       = aws_instance.web_server.public_ip
}