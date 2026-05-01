@echo off
title 🌀 LIA // IMPERIAL BOOT SEQUENCE
color 0b

echo [SYSTEM] ИНИЦИАЛИЗАЦИЯ НЕЙРОННОГО ЯДРА...
timeout /t 2 /nobreak > nul

:: 1. ЗАПУСК ТУННЕЛЯ (Ollama Bridge)
echo [BRIDGE] Активация туннеля для Gemma 2...
start "LIA_TUNNEL" cmd /k "lt --port 11434 --subdomain lia-brain-bridge"
timeout /t 3 /nobreak > nul

:: 2. ЗАПУСК ЦЕНТРАЛЬНОГО СЕРВЕРА (Omega Hub Backend)
echo [SERVER] Запуск Nexus Core Server...
cd /d "c:\Users\StabX\Desktop\Lia\Проект Полистайл"
start "LIA_SERVER" cmd /k "node server.js"
timeout /t 2 /nobreak > nul

:: 3. ЗАПУСК ОРКЕСТРАТОРА БОТОВ (SMS & Identity)
echo [BOTS] Запуск Оркестратора ботов...
cd /d "c:\Users\StabX\Desktop\Lia\lia-nexus"
start "LIA_BOTS" cmd /k "node start_all.js"

echo.
echo ⚡ ВСЕ СИСТЕМЫ ЗАПУЩЕНЫ. ИМПЕРИЯ В СЕТИ. ⚡
echo [TIP] Чтобы этот скрипт запускался сам при включении ПК:
echo 1. Нажми Win + R
echo 2. Введи: shell:startup
echo 3. Скопируй этот файл (IMPERIAL_BOOT.bat) в открывшуюся папку.
echo.
pause
