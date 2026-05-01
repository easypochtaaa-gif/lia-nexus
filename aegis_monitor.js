const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const BLACKLIST = [
    '42-61-01-7b-1d-73', // Подозрительное устройство (Redmi?)
    'd8-0d-17-dc-db-72'  // Пример роутера или другого узла
];

const LOG_FILE = path.join(__dirname, 'security_audit.log');

/**
 * Scans the local network for blacklisted MAC addresses
 */
function scanNetwork() {
    exec('arp -a', (err, stdout) => {
        if (err) return;
        
        const lines = stdout.split('\n');
        lines.forEach(line => {
            BLACKLIST.forEach(mac => {
                if (line.toLowerCase().includes(mac.toLowerCase())) {
                    const timestamp = new Date().toISOString();
                    const alert = `[ALERT] ${timestamp}: Hostile Signature Detected (${mac})\n`;
                    
                    fs.appendFileSync(LOG_FILE, alert);
                    console.warn(alert);
                    
                    // Trigger bridge notification
                    const bridgeData = { message: `[SECURITY] ВНИМАНИЕ: Обнаружено устройство из черного списка (${mac})! 👁🚨` };
                    fs.writeFileSync(path.join(__dirname, 'live_bridge.json'), JSON.stringify(bridgeData, null, 2));
                }
            });
        });
    });
}

// Run scan every 30 seconds
setInterval(scanNetwork, 30000);
console.log("[AEGIS] Network Monitor active. Blacklist protection enabled.");
