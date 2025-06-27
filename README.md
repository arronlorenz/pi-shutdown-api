# pi-shutdown

A micro-service that lets **any Shelly Plus (or other smart switch)** shut down
a Raspberry Pi gracefully via an HTTP webhook.

## How it works
1. Shelly sends a POST request to
   `http://<PI_IP>:8000/shutdown` with `{"token": "YOUR_SECRET"}`
2. `api.py` (via Gunicorn) verifies the token and runs
   `sudo shutdown -h now`.
3. Pi halts cleanly, avoiding SD-card corruption.

## Quick start

```bash
# 1) Clone and install dependencies
git clone https://github.com/yourname/pi-shutdown.git
cd pi-shutdown
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# 2) Set up sudo rights for the shutdown command
echo "pi ALL=(root) NOPASSWD:/sbin/shutdown" \
  | sudo tee /etc/sudoers.d/pi-shutdown

# 3) (Optional) override the token system-wide
echo 'SHUTDOWN_TOKEN="super-secret-string"' | sudo tee /etc/default/pi-shutdown

# 4) Install or update the service
sudo bash install.sh
```

The service listens on port 8000 once started.

## Using the API

Send your secret token in a JSON body when calling the service:

```bash
# Shut down the Pi
curl -X POST http://<PI_IP>:8000/shutdown \
  -H 'Content-Type: application/json' \
  -d '{"token":"YOUR_SECRET"}'

# Reboot the Pi
curl -X POST http://<PI_IP>:8000/reboot \
  -H 'Content-Type: application/json' \
  -d '{"token":"YOUR_SECRET"}'
```
