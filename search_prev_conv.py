import re

regex = r'[0-9]{8,11}:[a-zA-Z0-9_-]{34,40}'
filepath = r"C:\Users\StabX\.gemini\antigravity\brain\ce9f826a-89c4-449a-a490-be73b163574e\.system_generated\logs\transcript.jsonl"

print("Searching previous conversation logs...")
try:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            matches = re.findall(regex, line)
            if matches:
                print(f"Line {i+1} matches token: {matches}")
            if "stab_lia_bot" in line:
                print(f"Line {i+1} matches 'stab_lia_bot'")
except Exception as e:
    print(f"Error: {e}")
