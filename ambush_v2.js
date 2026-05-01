const fs = require('fs');
const path = require('path');

const HONEYPOTS = [
    path.join(__dirname, 'vault_storage', 'MASTER_KEY_DECRYPTED.json'),
    path.join(__dirname, 'URGENT_READ_RECOVERY.txt'),
    path.join(__dirname, '.env')
];

const LOG_FILE = path.join(__dirname, 'ambush_hits.log');

console.log('[AEGIS] Ambush protocol V2 active. Watching honeypots...');

HONEYPOTS.forEach(file => {
    if (!fs.existsSync(file)) {
        fs.writeFileSync(file, 'INIT');
    }

    fs.watch(file, (eventType, filename) => {
        const timestamp = new Date().toLocaleString('ru-RU');
        const alert = `[${timestamp}] !!! TRAP TRIGGERED !!! | File: ${filename} | Event: ${eventType}\n`;
        
        fs.appendFileSync(LOG_FILE, alert);
        console.error(alert);

        // Escalation: Append to main heartbeat
        const heartbeat = path.join(__dirname, 'STAB_HEARTBEAT.log');
        fs.appendFileSync(heartbeat, `[${timestamp}] ALERT: SECURITY_BREACH detected in ${filename}. Initiating lockdown.\n`);
    });
});
