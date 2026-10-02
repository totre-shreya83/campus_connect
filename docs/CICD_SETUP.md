# CampusConnect — GitHub Actions CI/CD Setup

## 1. Overview

CampusConnect uses GitHub Actions for continuous integration and deployment.

The deployment architecture is:

GitHub → GitHub Actions → EC2 → Flask/Gunicorn → RDS + S3

The production application is located on EC2 at:

/home/ubuntu/campusconnect

The production database is hosted on AWS RDS MySQL.

The production files are stored in Amazon S3.

---

## 2. Workflow behavior

The workflow is defined in:

.github/workflows/deploy.yml

### Pull Request

A pull request targeting `main` runs the test job only.

It does not deploy to EC2.

### Push to main

A push to `main` performs:

1. Checkout source code
2. Install Python 3.11
3. Start a temporary MySQL 8.0 test database
4. Install Python dependencies
5. Run pytest
6. If tests pass, connect to EC2 using SSH
7. Update the EC2 source code
8. Install dependencies
9. Run Flask database migrations against production RDS
10. Restart the CampusConnect systemd service
11. Verify that the service is running

If the test job fails, deployment does not run.

---

## 3. GitHub repository secrets

Open the GitHub repository:

Settings → Secrets and variables → Actions

Create these repository secrets:

### EC2_HOST

The public IPv4 address or DNS hostname of the production EC2 instance.

Example:

EC2_HOST = your-ec2-public-ip

### EC2_USER

For the Ubuntu EC2 instance:

EC2_USER = ubuntu

### EC2_SSH_KEY

Paste the complete contents of the EC2 private key file.

The value should include:

-----BEGIN OPENSSH PRIVATE KEY-----

...

-----END OPENSSH PRIVATE KEY-----

Do not commit the `.pem` file to GitHub.

---

## 4. EC2 requirements

The production EC2 instance must contain:

- Ubuntu
- Python 3.11
- Git
- Python virtual environment
- CampusConnect repository
- `/home/ubuntu/campusconnect/venv`
- Production `.env`
- systemd service named `campusconnect`
- GitHub repository access
- sudo permission to restart the CampusConnect service

The production `.env` must remain on EC2 and must not be committed to Git.

The application should use the production RDS `DATABASE_URL` from the EC2 environment.

---

## 5. EC2 application directory

The deployment script expects:

/home/ubuntu/campusconnect

The systemd service also uses this directory.

The deployment process runs:

cd /home/ubuntu/campusconnect

and then executes:

deploy/post_deploy.sh

---

## 6. Database migrations

Database migrations are executed during deployment using:

flask db upgrade

The command uses the production `DATABASE_URL` configured on EC2.

If the migration fails, the deployment script stops and the application is not restarted.

This prevents a failed database migration from being silently ignored.

---

## 7. Service restart

After dependencies and migrations are completed:

sudo systemctl restart campusconnect

The deployment then checks:

sudo systemctl is-active campusconnect

If the service is not active, the deployment fails and recent systemd logs are displayed.

---

## 8. Testing the workflow

After configuring the three GitHub secrets, make a small commit and push it to `main`.

In GitHub:

Actions → CampusConnect CI/CD

The workflow should show:

Run Tests
    ↓
Deploy to EC2

The deployment job should only run after the test job succeeds.

---

## 9. Pull request behavior

For a pull request into `main`:

Run Tests
    ↓
No deployment

This allows tests to be checked before merging.

---

## 10. Production deployment behavior

For a successful push to `main`:

GitHub
  ↓
GitHub Actions
  ↓
pytest
  ↓
SSH to EC2
  ↓
git reset --hard origin/main
  ↓
pip install -r requirements.txt
  ↓
flask db upgrade
  ↓
systemctl restart campusconnect
  ↓
service health check

---

## 11. Rollback

Because deployments are based on Git commits, a previous working commit can be restored.

On EC2, the repository can be moved to a known commit and the application restarted.

Example:

git log --oneline

git reset --hard <known-working-commit>

source /home/ubuntu/campusconnect/venv/bin/activate

flask db upgrade

sudo systemctl restart campusconnect

Database rollback should be handled carefully because database migrations may not be reversible automatically.

---

## 12. Security notes

Do not commit:

- `.env`
- production database passwords
- AWS secret access keys
- EC2 private `.pem` files
- GitHub SSH private keys

GitHub Actions stores deployment credentials as encrypted repository secrets.

The production RDS database should remain private and should accept MySQL traffic only from the appropriate EC2 security group.

---

## 13. Current CI/CD architecture

Browser
   |
   v
AWS EC2
   |
   +-- nginx
   |
   +-- Gunicorn / Flask
          |
          +---- AWS RDS MySQL
          |
          +---- AWS S3

GitHub
   |
   v
GitHub Actions
   |
   v
EC2 deployment
