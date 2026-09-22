# CampusConnect — AWS Deployment Runbook

## Architecture

Browser → nginx (port 80) → gunicorn (Unix socket) → Flask app → MySQL (local) + Amazon S3

MySQL runs on the same EC2 instance as the Flask application.

The current CampusConnect development S3 bucket is:

campusconnect-dev-shreya-2026

The production deployment will use a separate S3 bucket.

AWS credentials on EC2 will be provided through an IAM role instead of storing AWS access keys in the production `.env` file.

---

## 1. Launch the EC2 Instance

Recommended configuration:

- AMI: Ubuntu Server 22.04 LTS
- Region: Mumbai (`ap-south-1`)
- Instance type: t2.micro if available/eligible
- Storage: 20 GB gp3
- Create a new EC2 key pair and download the `.pem` file

---

## 2. Configure the Security Group

Required inbound rules:

| Type | Port | Source | Purpose |
|---|---:|---|---|
| SSH | 22 | Your IP only | EC2 administration |
| HTTP | 80 | 0.0.0.0/0 | Website |
| HTTPS | 443 | 0.0.0.0/0 | HTTPS |

Do not open port 3306 to the internet.

MySQL will run locally on the EC2 instance.

---

## 3. EC2 IAM Role

The EC2 instance will use an IAM role to access the CampusConnect production S3 bucket.

The application will not store AWS access keys on the server.

The IAM role will allow the required S3 operations for the CampusConnect production bucket.


## 4. Create the Production S3 Bucket

For production, create a separate S3 bucket.

Example production bucket name:

campusconnect-prod-shreya-2026

Use the Mumbai region (`ap-south-1`).

Do not use the development bucket for production data.

After creating the production bucket, enable S3 Versioning.

S3 Versioning protects files stored in the bucket by keeping previous versions of objects.

Important:

S3 Versioning protects files stored in S3. It does NOT back up the MySQL database.

The MySQL database will be backed up separately using the CampusConnect database backup script.

---

## 5. Create the EC2 IAM Role

Create an IAM role for EC2 with the trusted entity:

AWS service → EC2.

Example role name:

campusconnect-ec2-role

Attach a custom S3 policy that allows the CampusConnect application to access only the production bucket.

Use the following policy after replacing `BUCKET_NAME` with the actual production bucket name:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketVersioning"
      ],
      "Resource": "arn:aws:s3:::BUCKET_NAME"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::BUCKET_NAME/*"
    }
  ]
}