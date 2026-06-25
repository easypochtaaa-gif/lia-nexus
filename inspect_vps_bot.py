import paramiko
import sys

host = "80.89.237.50"
user = "root"
password = "57913123321oO!"

def inspect_vps():
    print("=== Inspecting VPS Docker/Compose/Env ===")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=10)
        
        commands = [
            "docker inspect lia_sovereign | grep -i token",
            "docker inspect lia_sovereign | grep -A 20 -i env",
            "cat /var/lib/lia_sovereign/upgrade/docker-compose.yml 2>/dev/null",
            "cat /var/lib/lia_sovereign/upgrade/.env 2>/dev/null",
            "ls -la /var/lib/lia_sovereign/upgrade/ 2>/dev/null",
            "docker logs --tail 50 lia_sovereign 2>&1"
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
    inspect_vps()
