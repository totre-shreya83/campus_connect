#!/bin/bash
set -e

cd /var/www/campusconnect

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p logs

if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi

export FLASK_APP=run.py
export FLASK_ENV=production

flask db upgrade || echo "Migration skipped"

sudo systemctl daemon-reload
sudo systemctl enable campusconnect
sudo systemctl start campusconnect

sudo systemctl status campusconnect --no-pager