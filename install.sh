#!/bin/bash
set -e

# Install or update the pi-shutdown service

DEST=/opt/pi-shutdown
SERVICE=pi-shutdown.service

# copy application files
sudo mkdir -p "$DEST"
# sync files excluding git directory and installer itself
sudo rsync -a --delete --exclude '.git' --exclude 'install.sh' ./ "$DEST"/

# install systemd service
sudo install -m 644 "$SERVICE" /etc/systemd/system/$SERVICE

# reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"

# restart service if running, otherwise start it
if sudo systemctl is-active --quiet "$SERVICE"; then
    sudo systemctl restart "$SERVICE"
else
    sudo systemctl start "$SERVICE"
fi

echo "Installation complete"
