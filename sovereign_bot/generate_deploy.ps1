$bytes = [IO.File]::ReadAllBytes('c:\Users\StabX\Desktop\Lia\sovereign_bot\sovereign_src.tar.gz')
$b64 = [Convert]::ToBase64String($bytes)
$template = @"
docker stop lia_sovereign || true
docker rm lia_sovereign || true
mkdir -p /var/lib/lia_sovereign/src
mkdir -p /var/lib/lia_sovereign/data
mkdir -p /var/lib/lia_sovereign/upgrade
echo 'THE_B64_PLACEHOLDER' | base64 -d > /tmp/sovereign_src.tar.gz
tar -xzf /tmp/sovereign_src.tar.gz -C /var/lib/lia_sovereign/src/
rm /tmp/sovereign_src.tar.gz
cat << 'EOF' > /var/lib/lia_sovereign/upgrade/docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:alpine
    container_name: lia_redis
    restart: always
    volumes:
      - redis_data:/data
    networks:
      - lia_network

  bot:
    image: python:3.11-slim
    container_name: lia_sovereign
    restart: always
    depends_on:
      - redis
    volumes:
      - /var/lib/lia_sovereign/data:/data
      - /var/lib/lia_sovereign/src:/src
    ports:
      - "8080:8080"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ADMIN_ID=7915004877
      - REDIS_HOST=redis
    networks:
      - lia_network
    command: >
      /bin/sh -c "
      pip install --no-cache-dir aiogram anthropic openai redis httpx pillow &&
      python -u /src/main.py
      "

networks:
  lia_network:
    driver: bridge

volumes:
  redis_data:
EOF
cd /var/lib/lia_sovereign/upgrade
docker compose down || true
docker compose up -d
"@
$content = $template.Replace('THE_B64_PLACEHOLDER', $b64)
[IO.File]::WriteAllText('c:\Users\StabX\Desktop\Lia\sovereign_bot\deploy_upgrade.txt', $content)
