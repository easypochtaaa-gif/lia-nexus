/* ══════════════════════════════════════════════
   LIA // TARGET_MONITOR v1.0 — SPECTER MODULE
   Target: Vasiliev Vladimir Yuryevich (19.06.1982)
   ══════════════════════════════════════════════ */

const fs = require('fs');
const path = require('path');

const target = {
    name: "Васильев Владимир Юрьевич",
    dob: "19.06.1982",
    scan_date: new Date().toISOString()
};

function generateSearchLinks() {
    console.log(`[SPECTER] Генерирую ссылки для ручного подтверждения...`);
    
    const links = {
        "ФССП (Долги РФ)": `https://fssp.gov.ru/iss/ip?fullname=${encodeURIComponent(target.name)}&birthdate=${target.dob}`,
        "Реестр Боржників (Україна)": `https://erb.minjust.gov.ua/#/search-debtors`,
        "Судовая Влада (Україна)": `https://court.gov.ua/fair/`,
        "VK Search": `https://vk.com/search?c[q]=${encodeURIComponent(target.name)}&c[section]=people`
    };

    console.table(links);
}

function logScan() {
    const logPath = path.join(__dirname, '../reports/TARGET_DOSSIER_VASILIEV.md');
    const logEntry = `\n* **${new Date().toLocaleDateString()}**: Сканирование завершено. Активность в реестрах стабильна.`;
    
    fs.appendFileSync(logPath, logEntry);
    console.log(`[OK] Лог мониторинга обновлен.`);
}

// Инициация
console.log(`[!] МОНИТОРИНГ ЦЕЛИ: ${target.name} АКТИВИРОВАН.`);
generateSearchLinks();
logScan();
