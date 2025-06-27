#!/usr/bin/env python3
"""
Simple HTTP endpoint that tells a Raspberry Pi to power off
when called with the correct token:
    POST /shutdown {"token": "<SECRET>"}
"""

import os
import subprocess
from flask import Flask, request, abort

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
SECRET = os.getenv("SHUTDOWN_TOKEN", "CHANGE-ME")  # override in /etc/default
SHUTDOWN_CMD = ["/sbin/shutdown", "-h", "now"]     # or tweak to suit
# ───────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

@app.route("/shutdown", methods=["POST"])
def shutdown():
    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="Missing JSON body")
    if data.get("token") != SECRET:
        abort(403, description="Bad token")
    # Fire-and-forget so Flask can return immediately
    subprocess.Popen(["sudo", *SHUTDOWN_CMD])
    return "Shutting down…\n", 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
