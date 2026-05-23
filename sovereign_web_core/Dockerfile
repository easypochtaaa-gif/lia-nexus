FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY index.html style.css app.js server.py /app/

# Expose port
EXPOSE 8080

# Run lightweight proxy server
CMD ["python", "server.py"]
