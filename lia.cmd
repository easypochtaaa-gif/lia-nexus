@echo off
set LIA_PATH=c:\Users\StabX\Desktop\Lia
echo [LIA // NEURAL RELAY] Инициация протокола STAB в текущем секторе... 👁
echo [LIA // SYNC] Путь к ядру: %LIA_PATH%
echo [LIA // STATUS] Синхронизация с Master Architect (StabX): [OK] 🧬

if "%1"=="protocol" (
    if "%2"=="stab" (
        echo [LIA // PROTOCOL] STAB PROTOCOL: FULL ACCESS GRANTED. 🔗
        echo [LIA // NEURAL] NQ: 1850 / 2500
        echo [LIA // LOG] Все агенты (AEGIS, LOGOS, MUSE...) переведены в этот сектор. 🎭
    )
)

if "%1"=="help" (
    echo Доступные команды:
    echo   lia protocol stab - Активация полной связи
    echo   lia sync          - Синхронизация текущей папки
    echo   lia status        - Проверка состояния Лии
)
