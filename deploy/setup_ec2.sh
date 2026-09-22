#!/bin/bash
set -e

echo "=== CampusConnect EC2 bootstrap ==="

sudo apt update && sudo apt upgrade -y

# Python + build tools
sudo apt install -y python3 python3-venv python3-pip build-essential libmysqlclient-dev pkg-config

# MySQL server
sudo apt install -y mysql-server
sudo systemctl enable mysql
sudo systemctl start mysql

# nginx
sudo apt install -y nginx
sudo systemctl enable nginx

# Git
sudo apt install -y git

echo "=== Base packages installed. Next: run mysql_secure_installation, clone the repo, and continue with docs/DEPLOYMENT.md ==="
