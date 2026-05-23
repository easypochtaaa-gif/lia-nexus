import base64
import os

files_to_pack = ["server.py", "index.html", "style.css", "app.js", "Dockerfile"]
core_dir = r"c:\Users\StabX\Desktop\Lia\sovereign_web_core"

out_lines = []
out_lines.append("mkdir -p sovereign_web_core && cd sovereign_web_core")

for filename in files_to_pack:
    filepath = os.path.join(core_dir, filename)
    if not os.path.exists(filepath):
        print(f"[ERROR]: File {filepath} not found!")
        continue
    with open(filepath, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode("utf-8")
    out_lines.append(f'echo "{b64_content}" | base64 -d > {filename}')

out_lines.append("docker rm -f lia_web_core 2>/dev/null")
out_lines.append("docker build -t lia_web_core .")
out_lines.append("docker run -d --name lia_web_core --restart always -p 80:8080 lia_web_core")
out_lines.append('echo "=== LIA SOVEREIGN WEB CORE V5.0 DEPLOYED SUCCESSFULLY ON PORT 80 ==="')

deploy_path = os.path.join(core_dir, "deploy_web.txt")
with open(deploy_path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(out_lines))

print("[PACKER]: Successfully compiled deploy_web.txt!")
