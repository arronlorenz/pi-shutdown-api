#!/usr/bin/env python
"""
Simple HTTP endpoint that tells a Raspberry Pi to power off
when called with the correct token via a GET request:
    /shutdown?token=<SECRET>
"""

import os
import subprocess
import logging
from flask import Flask, request, abort

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
SECRET = os.getenv("SHUTDOWN_TOKEN", "CHANGE-ME")  # override in /etc/default
SHUTDOWN_CMD = ["/sbin/shutdown", "-h", "now"]     # or tweak to suit
REBOOT_CMD = ["/sbin/shutdown", "-r", "now"]       # reboot the Pi
# ───────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/shutdown", methods=["GET"])
def shutdown():
    logger.info("Shutdown requested from %s", request.remote_addr)
    token = request.args.get("token")
    if token is None:
        abort(400, description="Missing token")
    if token != SECRET:
        abort(403, description="Bad token")
    cmd = ["sudo"] + SHUTDOWN_CMD
    logger.info("Executing command: %s", " ".join(cmd))
    try:
        subprocess.Popen(cmd)
        logger.info("Shutdown command launched successfully")
    except Exception:
        logger.exception("Shutdown command failed")
        abort(500, description="Failed to execute shutdown")
    return "Shutting down…\n", 202


@app.route("/reboot", methods=["GET"])
def reboot():
    logger.info("Reboot requested from %s", request.remote_addr)
    token = request.args.get("token")
    if token is None:
        abort(400, description="Missing token")
    if token != SECRET:
        abort(403, description="Bad token")
    cmd = ["sudo"] + REBOOT_CMD
    logger.info("Executing command: %s", " ".join(cmd))
    try:
        subprocess.Popen(cmd)
        logger.info("Reboot command launched successfully")
    except Exception:
        logger.exception("Reboot command failed")
        abort(500, description="Failed to execute reboot")
    return "Rebooting…\n", 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
