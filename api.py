#!/usr/bin/env python
"""
LAN-only HTTP endpoint that tells a Raspberry Pi to power off or reboot.

Preferred request (used by modern Shelly actions):
    POST /shutdown
    X-Auth-Token: <SECRET>

Legacy request (kept for the existing Shelly Plus 1 config at the drive-in;
logs a warning on use so we know when we can retire it):
    GET /shutdown?token=<SECRET>

Defense in depth is layered, not hinged on HTTP method:
  - the service runs as an unprivileged user with a narrow sudoers rule
    (see install.sh); `sudo shutdown` is the only elevated call it can make
  - the systemd unit allow-lists LAN + loopback IPs at the kernel level
  - the token is compared with `hmac.compare_digest` to avoid timing leaks
  - the service refuses to start if the token is missing or left at the
    `CHANGE-ME` placeholder
"""

import hmac
import logging
import os
import subprocess
import sys

from flask import Flask, request, abort

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
SECRET = os.getenv("SHUTDOWN_TOKEN", "")
SHUTDOWN_CMD = ["sudo", "-n", "/sbin/shutdown", "-h", "now"]
REBOOT_CMD = ["sudo", "-n", "/sbin/shutdown", "-r", "now"]
# ───────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

if not SECRET or SECRET == "CHANGE-ME":
    logger.error(
        "SHUTDOWN_TOKEN is missing or still set to 'CHANGE-ME'. "
        "Set it in /etc/default/pi-shutdown before starting the service."
    )
    sys.exit(1)

app = Flask(__name__)


def _extract_token():
    """Return the token provided with the request, or None."""
    header_token = request.headers.get("X-Auth-Token")
    if header_token:
        return header_token
    query_token = request.args.get("token")
    if query_token:
        logger.warning(
            "Legacy ?token= query param used from %s — migrate the caller "
            "to POST with an X-Auth-Token header",
            request.remote_addr,
        )
        return query_token
    return None


def _authorize():
    token = _extract_token()
    if token is None:
        abort(400, description="Missing token")
    if not hmac.compare_digest(token, SECRET):
        abort(403, description="Bad token")


def _fire(cmd, label):
    """Run the privileged shutdown/reboot command and verify it didn't
    immediately fail. The previous implementation logged "launched" the
    instant Popen returned, which masked silent sudo failures (e.g. when
    NoNewPrivileges blocked setuid escalation) — every log line said the
    operation succeeded while the kernel never received a reboot syscall.
    Capture stderr and wait briefly so a fast-failing child surfaces.
    """
    logger.info("Executing %s command", label)
    try:
        proc = subprocess.Popen(cmd, start_new_session=True,
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except Exception:
        logger.exception("%s command failed to spawn", label.capitalize())
        abort(500, description="Failed to spawn " + label)

    # /sbin/shutdown -h now signals init and exits within ~1s on success.
    # If it's still running after 5s without erroring, that's also fine —
    # the kernel will shortly tear us down.
    try:
        rc = proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.info("%s command running (no early exit) — assuming success",
                    label.capitalize())
        return

    if rc != 0:
        err = (proc.stderr.read() or b"").decode("utf-8", errors="replace").strip()
        logger.error("%s command exited %d: %s", label.capitalize(), rc, err or "(no stderr)")
        abort(500, description="Shutdown command failed (rc=%d)" % rc)

    logger.info("%s command exited 0", label.capitalize())


@app.route("/shutdown", methods=["GET", "POST"])
def shutdown():
    logger.info("Shutdown requested from %s (%s)", request.remote_addr, request.method)
    _authorize()
    _fire(SHUTDOWN_CMD, "shutdown")
    return "Shutting down\n", 202


@app.route("/reboot", methods=["GET", "POST"])
def reboot():
    logger.info("Reboot requested from %s (%s)", request.remote_addr, request.method)
    _authorize()
    _fire(REBOOT_CMD, "reboot")
    return "Rebooting\n", 202


@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok\n", 200
