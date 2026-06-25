import paramiko
import os

host = "80.89.237.50"
user = "root"
password = "57913123321oO!"
local_path = r"C:\Users\StabX\Desktop\Lia\sovereign_bot\main.py"
remote_path = "/var/lib/lia_sovereign/src/main.py"

def deploy():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password)
        
        sftp = ssh.open_sftp()
        print(f"Uploading {local_path} to {remote_path}...")
        sftp.put(local_path, remote_path)
        sftp.close()
        
        print("Restarting Docker container...")
        ssh.exec_command("docker restart lia_sovereign")
        print("Done.")
        
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deploy()
