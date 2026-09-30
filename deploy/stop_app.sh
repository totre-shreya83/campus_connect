#!/bin/bash
set -e

echo "=== Stopping CampusConnect ==="
sudo systemctl stop campusconnect || true
sleep 2
echo "Stopped"