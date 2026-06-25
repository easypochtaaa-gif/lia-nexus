# LIA // WEB CORE — Dockerfile
# Build context: ./sovereign_web_core/
# Serves cyberpunk dashboard + proxies chat to sovereign_bot backend
FROM python:3.12-slim

WORKDIR /app

# Copy all web files from the sovereign_web_core directory
COPY . /app/

# Expose port (default 8080)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run
CMD ["python", "-u", "server.py"]
