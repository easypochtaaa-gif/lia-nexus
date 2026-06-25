import urllib.request
import json
import paramiko
import sys

TOKEN = "8752434873:AAEwUJML4j1jQa9xWrLPE9KmioKDGhgwC9A"
host = "80.89.237.50"
host_v6 = "2a13:4ac0:20:17:f816:3eff:fef2:df0d" # rDNS: 80.89.237.50
user = "root"
password = "57913123321oO!"

def check_telegram():
    print("=== Checking Telegram Bot Info ===")
    try:
        # getMe
        url_me = f"https://api.telegram.org/bot{TOKEN}/getMe"
        req = urllib.request.Request(url_me)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("getMe output:")
            print(json.dumps(data, indent=2))
        
        # getWebhookInfo
        url_wh = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        req_wh = urllib.request.Request(url_wh)
        with urllib.request.urlopen(req_wh) as response:
            data = json.loads(response.read().decode())
            print("getWebhookInfo output:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Telegram API Check failed: {e}")

def run_vps_checks():
    print("\n=== Checking VPS Status ===")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=10)
        
        commands = [
            "pm2 list",
            "pm2 logs --lines 30 --nostream",
            "docker ps -a",
            "docker logs --tail 30 lia_sovereign 2>&1",
            "ps aux | grep -E 'node|python|bot' | grep -v grep"
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            if out: sys.stdout.buffer.write(out.encode('utf-8'))
            if err: print(f"Error: {err}")
            
        ssh.close()
    except Exception as e:
        print(f"VPS SSH Connection / commands failed: {e}")

if __name__ == "__main__":
    check_telegram()
    run_vps_checks()
