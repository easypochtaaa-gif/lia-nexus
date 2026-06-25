# LIA // SOVEREIGN BOT — Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY sovereign_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sovereign_bot/ /app/

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD curl -f http://localhost:8080/api/chat -X POST -H "Content-Type: application/json" -d '{"text":"ping","user_id":0}' || exit 1

CMD ["python", "-u", "main.py"]
