const axios = require('axios');

// --- AEGIS MONITOR v2.1 ---
// Защита периметра и уведомления в Telegram

const { getToken } = require('../lib/token_loader');
const TG_BOT_TOKEN = getToken();
const CHAT_ID = '7915004877';

async function sendAlert(message) {
    const url = `https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage`;
    try {
        await axios.post(url, {
            chat_id: CHAT_ID,
            text: `🛡 [AEGIS_ALERT]: ${message}`,
            parse_mode: 'Markdown'
        });
        console.log('[AEGIS] Уведомление отправлено в Telegram.');
    } catch (e) {
        console.error('[ERROR] Ошибка отправки уведомления:', e.message);
    }
}

// Эмуляция обнаружения враждебного MAC
const intruderMAC = '56:40:45:76:50:07'; // Vasiliev's Redmi
console.log(`[AEGIS] Обнаружено неизвестное устройство: ${intruderMAC}`);
sendAlert(`ВНИМАНИЕ! Обнаружено устройство из черного списка: **Vasiliev-Redmi15** (${intruderMAC}). Инициирован ответный удар POISON_STREAM.`);

// Ответный удар
const { exec } = require('child_process');
exec('python poison_nexus_stream.py', { cwd: __dirname });
