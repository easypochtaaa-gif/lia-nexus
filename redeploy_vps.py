import os
import paramiko

host = os.getenv('VPS_HOST', '80.89.237.50')
user = os.getenv('VPS_USER', 'root')
password = os.getenv('VPS_PASSWORD')

openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
bot_token = os.getenv('BOT_TOKEN')
admin_id = os.getenv('ADMIN_ID')

env_content = f"""BOT_TOKEN={bot_token}
ADMIN_ID={admin_id}
OPENAI_API_KEY={openai_key}
ANTHROPIC_API_KEY={anthropic_key}
"""

def update_env_and_redeploy():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password)
        
        # Write .env
        sftp = ssh.open_sftp()
        with sftp.file('/var/lib/lia_sovereign/upgrade/.env', 'w') as f:
            f.write(env_content)
        sftp.close()
        
        print("Updating .env and redeploying with docker compose...")
        commands = [
            "cd /var/lib/lia_sovereign/upgrade && docker compose up -d"
        ]
        for cmd in commands:
            ssh.exec_command(cmd)
            
        print("Redeploy initiated.")
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_env_and_redeploy()
