#!/usr/bin/env bash
# Quick fix when Nginx cannot read frontend/dist under /home/ubuntu (403 Forbidden).
# Run from repo root: chmod +x deploy/fix-frontend.sh && ./deploy/fix-frontend.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB_ROOT="/var/www/fleet"

cd "$REPO_ROOT"

if [[ ! -d frontend/dist ]]; then
  echo "frontend/dist missing — building..."
  cd frontend && npm install && npm run build && cd "$REPO_ROOT"
fi

sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete frontend/dist/ "$WEB_ROOT/"
sudo chown -R www-data:www-data "$WEB_ROOT"
sudo chmod -R a+rX "$WEB_ROOT"

sudo cp deploy/nginx-fleet.conf /etc/nginx/sites-available/fleet
sudo ln -sf /etc/nginx/sites-available/fleet /etc/nginx/sites-enabled/fleet
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "Static root: $WEB_ROOT"
curl -I http://127.0.0.1/ | head -5
echo "If HTTP/1.1 200 OK above, open port 80 in your EC2 security group and visit your public IP."
