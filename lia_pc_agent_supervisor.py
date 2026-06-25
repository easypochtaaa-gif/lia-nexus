"""
24/7 supervisor for LIA PC Agent. 
Restarts the agent if it crashes or exits.
"""
import subprocess
import sys
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = os.path.join(HERE, "lia_pc_agent.py")
LOG = os.path.join(HERE, "lia_pc_agent_supervisor.log")

def log_msg(msg):
    t = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{t}] {msg}\n"
    print(full_msg, end='')
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(full_msg)

def run_forever():
    log_msg("--- LIA SUPERVISOR STARTING ---")
    
    while True:
        log_msg(f"Launching Agent: {AGENT}")
        
        # Using sys.executable to ensure we use the same python interpreter
        process = subprocess.Popen([sys.executable, AGENT])
        
        # Wait for the process to exit
        process.wait()
        
        exit_code = process.returncode
        log_msg(f"Agent exited with code {exit_code}")
        
        if exit_code == 0:
            log_msg("Clean exit. Stopping supervisor.")
            break
        
        log_msg("Unexpected exit. Restarting in 10 seconds...")
        time.sleep(10)

if __name__ == "__main__":
    try:
        run_forever()
    except KeyboardInterrupt:
        log_msg("Supervisor stopped by user.")
