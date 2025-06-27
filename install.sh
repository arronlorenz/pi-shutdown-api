#!/bin/bash
set -e

# Install or update the pi-shutdown service

DEST=/opt/pi-shutdown
SERVICE=pi-shutdown.service

# Ensure script is running with root privileges
if [ "$EUID" -ne 0 ]; then
    echo "This installer must be run as root (e.g. via sudo bash install.sh)" >&2
    exit 1
fi

# copy application files
mkdir -p "$DEST"
# sync files excluding git directory and installer itself
rsync -a --delete --exclude '.git' --exclude 'install.sh' ./ "$DEST"/

# install systemd service
install -m 644 "$SERVICE" /etc/systemd/system/$SERVICE

# reload systemd and enable service
systemctl daemon-reload
systemctl enable "$SERVICE"

# restart service if running, otherwise start it
if systemctl is-active --quiet "$SERVICE"; then
    systemctl restart "$SERVICE"
else
    systemctl start "$SERVICE"
fi

echo "Installation complete"

