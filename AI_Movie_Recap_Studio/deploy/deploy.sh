#!/usr/bin/env bash
set -euo pipefail

echo "Deploying updates..."
cd /opt/AI_Movie_Recap_Studio
git pull origin main
source venv/bin/activate
pip install -r backend/requirements.txt
sudo systemctl restart ai-recap-backend
sudo systemctl restart ai-recap-worker
echo "Deployment finished."
