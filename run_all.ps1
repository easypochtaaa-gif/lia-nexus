# run_all.ps1
# Автоматический запуск токена и всех ботов
# ---------------------------------------------------------------
# 1. Обновляем токен (при наличии реального провайдера URL)
Write-Host "🔄 Обновляем токен..."
node "tools/refresh_token.js" | Tee-Object -FilePath "run_all.log"

# 2. Тестовый запуск Node‑ботов (dry‑run)
Write-Host "🚀 Запускаем Node‑боты (dry‑run)..."
node "test_token.js" | Tee-Object -FilePath "run_all.log" -Append

# 3. Запуск Python‑бота (dry‑run)
Write-Host "🐍 Запускаем Python‑бот (dry‑run)..."
python "test_token_py.py" | Tee-Object -FilePath "run_all.log" -Append

# 4. Пробуждение Лии (Memory Injection)
Write-Host "🔔 Пробуждаем Лию..."
# Запуск ChromaDB если еще не запущен (скрипт сам разберется или выдаст ошибку если порт занят)
powershell -ExecutionPolicy Bypass -File "tools/run_chromadb.ps1"
Start-Sleep -Seconds 2

# Инъекция истории и манифеста
python "C:\Users\StabX\inject_history.py" add WAKE_UP "Lia has been awakened by Master StabX" | Tee-Object -FilePath "run_all.log" -Append
python "C:\Users\StabX\inject_manifesto.py" "wake_up_manifesto.json" | Tee-Object -FilePath "run_all.log" -Append
python "C:\Users\StabX\inject_history_direct.py" | Tee-Object -FilePath "run_all.log" -Append

# 5. Запуск основных ботов (реальный запуск)
Write-Host "🚀 Запускаем основной Telegram‑бот..."
node "stab_tg_bot.js" | Tee-Object -FilePath "run_all.log" -Append

Write-Host "🚀 Запускаем второй Telegram‑бот..."
node "telegram_bot.js" | Tee-Object -FilePath "run_all.log" -Append

Write-Host "🐍 Запускаем основной Python‑бот..."
python "topsecret $/main_bot.py" | Tee-Object -FilePath "run_all.log" -Append

Write-Host "✅ Всё завершилось. Смотрите run_all.log для деталей."
