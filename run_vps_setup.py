import paramiko
import sys

host = "80.89.237.50"
user = "root"
password = "57913123321oO!"

def run_ssh_commands():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, timeout=10)
        
        commands = [
            "pm2 logs lia_web --lines 20 --nostream",
            "systemctl list-units --type=service --state=running | grep -i 'bot\\|lia\\|python'",
            "ps aux | grep -i 'python\\|node'"
        ]
        
        for cmd in commands:
            print(f"--- Running: {cmd} ---")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            if out: sys.stdout.buffer.write(out.encode('utf-8'))
            if err: print(f"Error: {err}")
            
        ssh.close()
    except Exception as e:
        print(f"SSH Exception: {e}")

if __name__ == "__main__":
    run_ssh_commands()
