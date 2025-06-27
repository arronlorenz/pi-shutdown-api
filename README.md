# pi-shutdown

Turn a **Shelly Plus** (or *any* device that can hit a webhook) into a safe-shutdown
button for your Raspberry Pi.  
A tiny Flask app, served by **Gunicorn**, listens on port&nbsp;**8000**. When it
receives a signed POST request it executes `sudo shutdown -h now`, halting the
Pi cleanly and protecting your SD card.

---

## How it works

1. **Shelly Action** → sends  
   `POST http://<PI_IP>:8000/shutdown`  
   with JSON body `{ "token": "YOUR_SECRET" }`.
2. **`api.py`** validates the token.
3. The script forks `sudo shutdown -h now` (or `reboot`), returns `202 Accepted`,
   and Gunicorn stays up while the kernel powers down.

---

## Quick-start

```bash
# 1) Clone and install dependencies (as root)
git clone https://github.com/yourname/pi-shutdown.git
cd pi-shutdown
pip install -r requirements.txt

# 2) (Optional) set a custom token system-wide
echo 'SHUTDOWN_TOKEN="super-secret-string"' \
  | sudo tee /etc/default/pi-shutdown

# 3) Install / update and start the systemd service
sudo bash install.sh
