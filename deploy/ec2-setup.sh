#!/usr/bin/env bash
# EC2 one-box deploy (Ubuntu 22.04). Run from repo root after cloning:
#   chmod +x deploy/ec2-setup.sh && ./deploy/ec2-setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Installing system packages..."
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip nginx curl

if ! command -v node >/dev/null 2>&1 || [[ "$(node -v)" != v20* ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

echo "==> Python backend..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Frontend build..."
cd frontend
npm install
npm run build
cd "$REPO_ROOT"

echo "==> systemd service..."
sudo cp deploy/fleet-api.service /etc/systemd/system/fleet-api.service
sudo systemctl daemon-reload
sudo systemctl enable fleet-api
sudo systemctl restart fleet-api

echo "==> Nginx..."
sudo cp deploy/nginx-fleet.conf /etc/nginx/sites-available/fleet
sudo ln -sf /etc/nginx/sites-available/fleet /etc/nginx/sites-enabled/fleet
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "Deploy complete. Open: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo YOUR_EC2_PUBLIC_IP)"
echo "Logs: sudo journalctl -u fleet-api -f"
