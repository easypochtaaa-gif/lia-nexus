import os
import re

regex = r'[0-9]{8,11}:[a-zA-Z0-9_-]{34,40}'
dir_to_search = r"C:\Users\StabX\Desktop\Lia"

print(f"Searching for bot tokens in {dir_to_search}...")
found_tokens = {}

for root, dirs, files in os.walk(dir_to_search):
    # skip node_modules and .git
    if "node_modules" in root or ".git" in root or ".gemini" in root:
        continue
    for file in files:
        if file.endswith(('.js', '.py', '.env', '.json', '.txt', '.html', '.sh', '.ps1', '.bat')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    matches = re.findall(regex, content)
                    if matches:
                        found_tokens[filepath] = matches
            except Exception as e:
                pass

for filepath, tokens in found_tokens.items():
    print(f"File: {filepath}")
    for token in tokens:
        print(f"  Token: {token}")
