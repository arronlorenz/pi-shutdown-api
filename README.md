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
| **1. Shelly fires an action** | You press/hold the input or the relay switches off. | `GET http://192.168.4.25:8000/shutdown?token=super-secret` |
| **2. `api.py` checks the token** | Token is compared with `SHUTDOWN_TOKEN` (default `CHANGE-ME`). | — |
| **3. Pi shuts down or reboots** | Script forks `sudo shutdown -h now` (or `reboot`). | HTTP **202 Accepted** is returned; Gunicorn exits only when the kernel halts. |

---

## Complete webhook URLs

| Purpose | Method | Full URL to paste in Shelly “Actions” |
|---------|--------|---------------------------------------|
| **Shut down** | **GET** | `http://<PI_IP>:8000/shutdown?token=YOUR_SECRET` |
| **Reboot** | **GET** | `http://<PI_IP>:8000/reboot?token=YOUR_SECRET` |

> **Tip:** Replace `<PI_IP>` with your Pi’s address (e.g. `192.168.4.25`) and
> keep the secret string identical to the one in `/etc/default/pi-shutdown`.

---

## Requirements

The scripts are compatible with **Python 2.7.16** and **Python 3.7.3**.

## Quick-start

```bash
# 1) Grab the code and install Python deps (Python 2.7 or 3.7)
git clone https://github.com/arronlorenz/pi-shutdown-api.git
cd pi-shutdown-api
sudo pip install -r requirements.txt        # Flask + Gunicorn

# 2) Install/upgrade the systemd unit and start it
sudo bash install.sh        # prompts for your secret token
```

Running `install.sh` again updates the files in place. The script stops the
existing service, installs the new version, and then starts it back up.

---

## ⚠️ Hardening trap — don't put these back

The systemd unit is *intentionally* missing two flags that look like
they belong on a "least-privilege" service. They were added once
(`a873e05`, 2026-04-30) and silently broke the Pi-halt path until
2026-05-01:

- **`NoNewPrivileges=true`** — kernel flag that blocks setuid-based
  privilege escalation for the process and every child, *forever in
  that process tree*. The api shells out to `sudo -n /sbin/shutdown`,
  and sudo's whole mechanism is setuid. NNP makes `sudo` exit
  non-zero before it ever runs `/sbin/shutdown`. Result: the api
  returns HTTP 202, logs "Shutdown command launched," and the Pi
  stays up.
- **`SystemCallFilter=~@reboot`** — denylists the `reboot(2)` family.
  Even if sudo escalation worked, the kernel call `/sbin/shutdown`
  ultimately makes would be killed by SIGSYS. Same silent outcome.

The previous `_fire()` masked both failures by redirecting stderr to
`/dev/null` and logging "launched" the instant `Popen` returned.
`_fire()` now `wait()`s on the child for 5 s and surfaces a non-zero
exit (with stderr) as a 500 — so if NNP/reboot-filter ever creep back
in, the api will tell you instead of lying. Don't undo that, either.

Every other hardening flag in `pi-shutdown.service` is fine to keep
or extend (LAN allow-list, dedicated user, `ProtectSystem`,
`RestrictAddressFamilies`, `MemoryDenyWriteExecute`, etc.). The two
above are the only ones that conflict with the function of this
service.
