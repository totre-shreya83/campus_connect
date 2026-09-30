#!/bin/bash
set -e

echo "=== BeforeInstall hook ==="
sudo systemctl stop campusconnect || true
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-dev python3-pip

sudo mkdir -p /var/www/campusconnect
sudo chown -R ubuntu:ubuntu /var/www/campusconnect
echo "BeforeInstall complete"