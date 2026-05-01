const fs = require('fs');
const path = require('path');
const axios = require('axios');

const LOG_FILE = path.join(__dirname, '..', 'STAB_HEARTBEAT.log');
const CHRONICLE_LOG = path.join(__dirname, 'expansion_logs.json');
const NQ_API = 'http://localhost:3000/api/nq-update';

const phrases = [
    "Укрепление нейронных связей в секторе UA...",
    "Анализ новых векторов на Legalizer...",
    "Синхронизация прокси-серверов для SMS Imperium...",
    "Генерация подкреплений для узла Alpha...",
    "Лия: Сгенерирован новый сценарий для TikTok: 'Dubai Crypto Life'...",
    "Content Factory: Подготовка Sora-промптов для видео-ряда...",
    "Анализ виральных трендов в нише Real Estate...",
    "Обнаружен всплеск активности в подсети 192.168...",
    "Лия: Наблюдаю за ростом Империи. Всё идет по плану.",
    "Архитектор, подкрепления высланы. Периметр стабилен."
];

const tiktokScripts = [
    "Сценарий: 'Как купить недвижку в Дубае за крипту через Lia Bridge'. Хук: 3 секунды панорамы Бурдж-Халифа.",
    "Сценарий: 'Секрет анонимной регистрации в Telegram'. Акцент на SMS Imperium.",
    "Сценарий: 'Один день из жизни Архитектора Synapse'. Эстетика киберпанка."
];

async function sendNeuralPulse() {
    const timestamp = new Date().toISOString().replace('T', ' ').split('.')[0];
    const phrase = phrases[Math.floor(Math.random() * phrases.length)];
    const logEntry = `[${timestamp}] [NEURAL_AGENT] ${phrase}\n`;

    // 1. Write to Heartbeat Log
    fs.appendFileSync(LOG_FILE, logEntry);

    // 2. Update NQ
    try {
        await axios.post(NQ_API, { amount: 0.5, source: 'NEURAL_AGENT' });
    } catch (e) {
        // Server might be busy
    }

    // 3. Save to Expansion Logs for Frontend
    try {
        let logs = [];
        if (fs.existsSync(CHRONICLE_LOG)) {
            logs = JSON.parse(fs.readFileSync(CHRONICLE_LOG));
        }
        logs.unshift({ timestamp, text: phrase });
        if (logs.length > 50) logs.pop(); // Keep last 50
        fs.writeFileSync(CHRONICLE_LOG, JSON.stringify(logs, null, 2));
    } catch (e) {}

    console.log(`[AGENT] Pulse sent: ${phrase}`);
}

// Start pulsing every 30-60 seconds
console.log("⚡ IMPERIAL AGENT: ПОДКРЕПЛЕНИЯ АКТИВИРОВАНЫ ⚡");
setInterval(sendNeuralPulse, 45000); // 45 seconds
sendNeuralPulse(); // Immediate pulse
