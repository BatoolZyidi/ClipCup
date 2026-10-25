# AWS EC2 Deployment Guide for Clip Cup

This guide documents deploying Clip Cup to AWS EC2 using Docker and AWS IAM roles for secure credential-free access to Amazon Bedrock and Amazon S3.

---

## 1. Architecture & EC2 Instance Recommendation

- **Recommended Instance Type**: `c6i.large` (2 vCPU, 4GB RAM) or `c6i.xlarge` (4 vCPU, 8GB RAM). Video rendering with FFmpeg and OpenCV face detection benefits from compute-optimized CPU cores.
- **AMI**: Ubuntu Server 24.04 LTS (HVM), SSD Volume Type.
- **Storage**: 30 GB gp3 EBS root volume (for temporary video processing caches).

---

## 2. IAM Role for EC2 (No Secrets on Disk)

Instead of hardcoding AWS access keys in `.env` on the server, attach an IAM Role to your EC2 instance with least-privilege permissions for Amazon S3 and Amazon Bedrock.

### S3 & Bedrock IAM Policy (`ClipCupEC2Policy`)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:foundation-model/*"
      ]
    },
    {
      "Sid": "S3ShortsBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:AbortMultipartUpload"
      ],
      "Resource": "arn:aws:s3:::YOUR_S3_BUCKET_NAME/shorts/*"
    }
  ]
}
```

1. In the AWS IAM Console, create a role for **EC2** and attach this policy.
2. In the EC2 Console, select your instance -> **Actions** -> **Security** -> **Modify IAM Role** -> Select `ClipCupEC2Role`.
3. With this role attached, boto3 will automatically retrieve temporary credentials via the EC2 Instance Metadata Service (IMDSv2). Leave `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` blank in `.env`.

---

## 3. Security Group Configuration

Configure your EC2 Security Group with the following inbound rules:

| Type | Protocol | Port Range | Source | Purpose |
|------|----------|------------|--------|---------|
| SSH | TCP | 22 | Your IP / Bastion | Secure SSH access |
| HTTP | TCP | 80 | `0.0.0.0/0` | Web traffic & Let's Encrypt renewal |
| HTTPS | TCP | 443 | `0.0.0.0/0` | Secure SSL/TLS web traffic |

---

## 4. Host Setup & Docker Deployment

### Step A: Install Docker & Compose on the Instance
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

### Step B: Clone Repository & Configure Environment
```bash
git clone https://github.com/your-username/ClipCup.git
cd ClipCup
cp .env.example .env
nano .env
```
Fill in `.env`:
```ini
SECRET_KEY=generate-a-strong-random-key-for-prod
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-ec2-public-ip
S3_BUCKET_NAME=your-clipcup-bucket
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
```

### Step C: Build and Run with Docker Compose
```bash
docker compose up -d --build backend
```

---

## 5. HTTPS Setup with Nginx & Certbot

It is critical that production video uploads and API requests are encrypted over HTTPS.

### Install Nginx & Certbot
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Nginx Reverse Proxy Configuration (`/etc/nginx/sites-available/clipcup`)
```nginx
server {
    server_name your-domain.com;

    client_max_body_size 500M; # Support long video uploads

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 900s; # 15 min pipeline timeout
        proxy_connect_timeout 900s;
    }
}
```

Enable site and acquire SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/clipcup /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```
Certbot automatically provisions an SSL certificate and configures HTTP-to-HTTPS redirection.
