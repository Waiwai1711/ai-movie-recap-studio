#!/usr/bin/env bash
set -euo pipefail

echo "Setting up AI Movie Recap Studio..."
sudo apt-get update && sudo apt-get install -y \
    python3 python3-pip python3-venv ffmpeg curl git caddy \
    fonts-noto-core fonts-sil-padauk

INSTALL_DIR="/opt/AI_Movie_Recap_Studio"
sudo mkdir -p $INSTALL_DIR
sudo chown -R $USER:$USER $INSTALL_DIR
cd $INSTALL_DIR

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
mkdir -p storage/users
chmod -R 750 storage

echo "Setup completed."
