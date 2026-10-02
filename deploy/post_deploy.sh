#!/bin/bash
set -e

APP_DIR="/var/www/campusconnect"

echo "========================================"
echo "CampusConnect Post-Deployment"
echo "========================================"

cd "$APP_DIR"

echo "=== Updating source code ==="
git fetch origin main
git reset --hard origin/main

echo "=== Activating virtual environment ==="
source "$APP_DIR/venv/bin/activate"

echo "=== Loading production environment ==="
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env"
    set +a
else
    echo "Production .env file not found."
    exit 1
fi

if [ -z "${DATABASE_URL:-}" ]; then
    echo "DATABASE_URL is not configured."
    exit 1
fi

echo "=== Installing dependencies ==="
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "=== Running database migrations ==="
export FLASK_APP=run.py
export FLASK_ENV=production
flask db upgrade

echo "=== Restarting CampusConnect ==="
sudo systemctl daemon-reload
sudo systemctl restart campusconnect

echo "=== Waiting for service ==="
sleep 3

echo "=== Checking service status ==="
if sudo systemctl is-active --quiet campusconnect; then
    echo "CampusConnect service is running."
else
    echo "CampusConnect service failed to start."
    sudo systemctl status campusconnect --no-pager || true
    sudo journalctl -u campusconnect -n 50 --no-pager || true
    exit 1
fi

echo "========================================"
echo "Deployment completed successfully."
echo "========================================"
