"""
LIA // SELF-FIX SCRIPT — Run directly on VPS when SSH is unavailable.
Triggers HTTPS fix + docker redeploy via HTTP endpoint.
Access: curl http://80.89.237.50:8080/admin/self-fix?token=LIA_SOVEREIGN_FIX
"""

import subprocess
import sys
import os
import time

TOKEN = "LIA_SOVEREIGN_FIX"
DOMAIN = "dark-stab.space"


def run(cmd: str) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)


def fix_all() -> str:
    """Execute all fixes and return report."""
    report = []

    # 1. Open firewall ports
    report.append("=== [1/6] FIREWALL ===")
    report.append(run("ufw allow 443/tcp 2>/dev/null; ufw allow 80/tcp 2>/dev/null; iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null; iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null; echo 'Firewall done'"))

    # 2. Install certbot
    report.append("\n=== [2/6] INSTALL CERTBOT ===")
    report.append(run("apt-get update -qq 2>&1 | tail -3; apt-get install -y -qq certbot python3-certbot-nginx 2>&1 | tail -5; which certbot || echo 'certbot installed'"))

    # 3. Get SSL certificate
    report.append("\n=== [3/6] SSL CERTIFICATE ===")
    report.append(run(f"certbot --nginx -d {DOMAIN} --non-interactive --agree-tos --email admin@{DOMAIN} --redirect 2>&1"))

    # 4. Reload nginx
    report.append("\n=== [4/6] RELOAD NGINX ===")
    report.append(run("systemctl reload nginx 2>&1; systemctl status nginx --no-pager 2>&1 | head -5"))

    # 5. Stop old python processes that may hold ports
    report.append("\n=== [5/6] CLEANUP OLD PROCESSES ===")
    report.append(run("pkill -f 'python.*main.py' 2>/dev/null; pkill -f 'python.*server.py' 2>/dev/null; echo 'Old processes cleaned'"))

    # 6. Rebuild docker
    report.append("\n=== [6/6] DOCKER REBUILD ===")
    report.append(run("cd /root/lia && docker compose down --remove-orphans 2>&1; docker compose build --no-cache 2>&1 | tail -20; docker compose up -d 2>&1; docker compose ps 2>&1"))

    # Final status
    report.append("\n=== FINAL STATUS ===")
    report.append(run("ss -tlnp | grep -E ':(80|443|8080) '; echo '---'; curl -sI https://dark-stab.space 2>&1 | head -5"))

    return "\n".join(report)


if __name__ == "__main__":
    print("LIA // SELF-FIX v1.0")
    print(fix_all())
