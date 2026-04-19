#!/bin/bash
set -euo pipefail

# Install or update the pi-shutdown service.

DEST=/opt/pi-shutdown
SERVICE=pi-shutdown.service
TOKEN_FILE=/etc/default/pi-shutdown
SUDOERS_FILE=/etc/sudoers.d/pi-shutdown
RUN_USER=pishutdown

if [ "$EUID" -ne 0 ]; then
    echo "This installer must be run as root (e.g. via sudo bash install.sh)" >&2
    exit 1
fi

# Stop service before updating files so a running worker doesn't hold old code.
if systemctl is-active --quiet "$SERVICE"; then
    systemctl stop "$SERVICE"
fi

# 1) Dedicated unprivileged system user to run the Flask app.
if ! id -u "$RUN_USER" >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$RUN_USER"
fi

# 2) Shutdown token. Parse the existing file with grep (never `source`, so a
#    tampered file can't execute arbitrary shell under root).
CURRENT_TOKEN=""
if [ -f "$TOKEN_FILE" ]; then
    CURRENT_TOKEN="$(grep -E '^SHUTDOWN_TOKEN=' "$TOKEN_FILE" | head -n1 | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//' || true)"
fi
PROMPT_DEFAULT="${CURRENT_TOKEN:-<none>}"
read -r -p "Enter shutdown token [${PROMPT_DEFAULT}]: " TOKEN_INPUT
TOKEN="${TOKEN_INPUT:-$CURRENT_TOKEN}"
if [ -z "$TOKEN" ] || [ "$TOKEN" = "CHANGE-ME" ]; then
    echo "Refusing to install with an empty or 'CHANGE-ME' token." >&2
    exit 1
fi

umask 077
printf 'SHUTDOWN_TOKEN="%s"\n' "$TOKEN" > "$TOKEN_FILE"
# EnvironmentFile= is read by systemd (root) before User= takes effect,
# so root:root / 600 is enough — no read access is needed from the
# unprivileged service user.
chown root:root "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"

# 3) Application files, owned by root, readable by the service user.
mkdir -p "$DEST"
rsync -a --delete --exclude '.git' --exclude 'install.sh' ./ "$DEST"/
chown -R root:"$RUN_USER" "$DEST"
chmod -R g+rX,o-rwx "$DEST"

# 4) Narrow sudoers rule — only the two shutdown invocations, nothing else.
cat > "$SUDOERS_FILE" <<EOF
$RUN_USER ALL=(root) NOPASSWD: /sbin/shutdown -h now, /sbin/shutdown -r now
EOF
chmod 440 "$SUDOERS_FILE"
if ! visudo -cf "$SUDOERS_FILE" >/dev/null; then
    echo "Generated sudoers file failed validation; removing." >&2
    rm -f "$SUDOERS_FILE"
    exit 1
fi

# 5) systemd unit.
install -m 644 "$SERVICE" /etc/systemd/system/"$SERVICE"
systemctl daemon-reload
systemctl enable "$SERVICE"

if systemctl is-active --quiet "$SERVICE"; then
    systemctl restart "$SERVICE"
else
    systemctl start "$SERVICE"
fi

echo "Installation complete. Preferred request format:"
echo "  curl -X POST -H 'X-Auth-Token: <TOKEN>' http://<PI_IP>:8000/shutdown"
