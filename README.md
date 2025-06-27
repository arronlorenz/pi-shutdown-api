# pi-shutdown

Turn a **Shelly Plus** (or *any* gadget that can call a webhook) into a one-tap,
graceful shutdown switch for your Raspberry Pi.

A tiny Flask app served by **Gunicorn** listens on port **8000**.  
When it receives a signed request it runs `sudo shutdown -h now`, helping you
avoid SD-card corruption.

---

## How it works

| Step | What happens | Example |
|------|--------------|---------|
| **1. Shelly fires an action** | You press/hold the input or the relay switches off. | `POST http://192.168.4.25:8000/shutdown` with body `{"token":"super-secret"}` **or**<br>`GET  http://192.168.4.25:8000/shutdown?token=super-secret` |
| **2. `api.py` checks the token** | Token is compared with `SHUTDOWN_TOKEN` (default `CHANGE-ME`). | — |
| **3. Pi shuts down or reboots** | Script forks `sudo shutdown -h now` (or `reboot`). | HTTP **202 Accepted** is returned; Gunicorn exits only when the kernel halts. |

---

## Complete webhook URLs

| Purpose | Method | Full URL to paste in Shelly “Actions” |
|---------|--------|---------------------------------------|
| **Shut down (GET)** | **GET** | `http://<PI_IP>:8000/shutdown?token=YOUR_SECRET` |
| **Shut down (JSON)** | **POST** | `http://<PI_IP>:8000/shutdown`<br>Body → `{"token":"YOUR_SECRET"}` |
| **Reboot (GET)** | **GET** | `http://<PI_IP>:8000/reboot?token=YOUR_SECRET` |
| **Reboot (JSON)** | **POST** | `http://<PI_IP>:8000/reboot`<br>Body → `{"token":"YOUR_SECRET"}` |

> **Tip:** Replace `<PI_IP>` with your Pi’s address (e.g. `192.168.4.25`) and
> keep the secret string identical to the one in `/etc/default/pi-shutdown`.

---

## Quick-start

```bash
# 1) Grab the code and install Python deps (as root or in a venv)
git clone https://github.com/yourname/pi-shutdown.git
cd pi-shutdown
pip install -r requirements.txt        # Flask + Gunicorn

# 2) (Optional) set your own secret
echo 'SHUTDOWN_TOKEN="super-secret"' | sudo tee /etc/default/pi-shutdown

# 3) Install/upgrade the systemd unit and start it
sudo bash install.sh
