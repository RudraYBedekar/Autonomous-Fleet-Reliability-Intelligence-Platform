#!/usr/bin/env bash
# EC2 one-box deploy (Ubuntu 22.04). Run from repo root after cloning:
#   chmod +x deploy/ec2-setup.sh && ./deploy/ec2-setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

WEB_ROOT="/var/www/fleet"

get_public_ip() {
  local token=""
  token="$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null || true)"
  if [[ -n "$token" ]]; then
    curl -sf -H "X-aws-ec2-metadata-token: $token" \
      "http://169.254.169.254/latest/meta-data/public-ipv4" 2>/dev/null || true
    return
  fi
  curl -sf "https://checkip.amazonaws.com" 2>/dev/null | tr -d '[:space:]' || true
}

echo "==> Installing system packages..."
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip nginx curl rsync

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

echo "==> Publishing static files to ${WEB_ROOT}..."
sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete frontend/dist/ "$WEB_ROOT/"
sudo chown -R www-data:www-data "$WEB_ROOT"
sudo chmod -R a+rX "$WEB_ROOT"

echo "==> systemd service..."
sed "s|@REPO_ROOT@|${REPO_ROOT}|g" deploy/fleet-api.service | sudo tee /etc/systemd/system/fleet-api.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable fleet-api
sudo systemctl restart fleet-api

echo "==> Nginx..."
sudo cp deploy/nginx-fleet.conf /etc/nginx/sites-available/fleet
sudo ln -sf /etc/nginx/sites-available/fleet /etc/nginx/sites-enabled/fleet
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "==> Health checks..."
sleep 2
if ! curl -sf "http://127.0.0.1:8000/" > /dev/null; then
  echo "ERROR: FastAPI is not responding on port 8000."
  sudo journalctl -u fleet-api -n 40 --no-pager || true
  exit 1
fi

if ! curl -sf "http://127.0.0.1/" | grep -q '<div id="root">'; then
  echo "ERROR: Nginx is not serving the frontend."
  sudo tail -30 /var/log/nginx/error.log || true
  exit 1
fi

PUBLIC_IP="$(get_public_ip)"
PUBLIC_IP="${PUBLIC_IP:-YOUR_EC2_PUBLIC_IP}"

echo ""
echo "Deploy complete. Open: http://${PUBLIC_IP}"
echo "Logs: sudo journalctl -u fleet-api -f"
echo "Nginx errors: sudo tail -f /var/log/nginx/error.log"
