import os

dir_to_search = r"C:\Users\StabX\Desktop\Lia"
search_str = "stab_lia_bot"

print(f"Searching for '{search_str}' in {dir_to_search}...")
for root, dirs, files in os.walk(dir_to_search):
    if "node_modules" in root or ".git" in root or ".gemini" in root:
        continue
    for file in files:
        if file.endswith(('.js', '.py', '.env', '.json', '.txt', '.html', '.sh', '.ps1', '.bat', '.md')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if search_str in content:
                        print(f"Found in: {filepath}")
                        # print matching lines
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if search_str in line:
                                print(f"  Line {i+1}: {line}")
            except Exception as e:
                pass
