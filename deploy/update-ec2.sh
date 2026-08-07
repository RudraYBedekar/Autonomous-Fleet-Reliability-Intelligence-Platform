#!/usr/bin/env bash
# Pull latest code, rebuild frontend, restart services. Run on EC2 from repo root:
#   chmod +x deploy/update-ec2.sh && ./deploy/update-ec2.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
WEB_ROOT="/var/www/fleet"

echo "==> Syncing code from GitHub..."
git fetch origin main
git reset --hard origin/main

echo "==> Python deps..."
source venv/bin/activate
pip install -q -r requirements.txt

echo "==> Frontend build..."
cd frontend
npm install
npm run build
cd "$REPO_ROOT"

echo "==> Publish static files..."
sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete frontend/dist/ "$WEB_ROOT/"
sudo chown -R www-data:www-data "$WEB_ROOT"
sudo chmod -R a+rX "$WEB_ROOT"

echo "==> Restart services..."
sed "s|@REPO_ROOT@|${REPO_ROOT}|g" deploy/fleet-api.service | sudo tee /etc/systemd/system/fleet-api.service > /dev/null
sudo cp deploy/nginx-fleet.conf /etc/nginx/sites-available/fleet
sudo ln -sf /etc/nginx/sites-available/fleet /etc/nginx/sites-enabled/fleet
sudo systemctl daemon-reload
sudo systemctl restart fleet-api
sudo nginx -t
sudo systemctl restart nginx

sleep 2
curl -sf "http://127.0.0.1:8000/" > /dev/null
curl -sf "http://127.0.0.1/" | grep -q '<div id="root">'

PUBLIC_IP="$(curl -sf https://checkip.amazonaws.com 2>/dev/null | tr -d '[:space:]' || echo 'YOUR_EC2_PUBLIC_IP')"
echo ""
echo "Update complete. Open: http://${PUBLIC_IP}"
echo "Hard refresh browser: Ctrl+Shift+R"
