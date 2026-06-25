# run_chromadb.ps1
# Запуск локального сервера Chromadb (порт 8000)
# Требует установленный пакет `chromadb` (pip install chromadb)
# Если chromadb не установлен, установите его вручную.

Write-Host "🚀 Запускаем Chromadb сервер..."
# Запускаем в фоне, чтобы не блокировать скрипт
Start-Process -FilePath "chroma" -ArgumentList "run", "--host", "localhost", "--port", "8000" -NoNewWindow
Start-Sleep -Seconds 10  # Увеличиваем паузу для стабильности
Write-Host "✅ Chromadb сервер запущен на http://localhost:8000"
