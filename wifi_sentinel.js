const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(__dirname, 'wifi_sentinel.log');
const HEARTBEAT = path.join(__dirname, 'STAB_HEARTBEAT.log');

const WHITELIST_FILE = path.join(__dirname, 'whitelist.json');
let knownDevices = new Set();

function getWhitelist() {
    try {
        return JSON.parse(fs.readFileSync(WHITELIST_FILE, 'utf8'));
    } catch (e) {
        return {};
    }
}

function scanNetwork() {
    const whitelist = getWhitelist();
    exec('arp -a', (err, stdout, stderr) => {
        const timestamp = new Date().toLocaleString('ru-RU');
        const lines = stdout.split('\n');
        
        lines.forEach(line => {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 2 && parts[0].match(/^192\.168\.0\.\d+$/)) {
                const ip = parts[0];
                const mac = parts[1];
                
                if (mac && mac.includes('-') && !knownDevices.has(mac)) {
                    knownDevices.add(mac);
                    const deviceName = whitelist[mac.toLowerCase()] || 'UNKNOWN_POTENTIAL_THREAT';
                    const isFriendly = !!whitelist[mac.toLowerCase()];
                    
                    const status = isFriendly ? '[FRIENDLY]' : '[!] THREAT_DETECTED';
                    const msg = `[${timestamp}] ${status} | Device: ${deviceName} | IP: ${ip} | MAC: ${mac}\n`;
                    
                    fs.appendFileSync(LOG_FILE, msg);
                    
                    if (!isFriendly) {
                        fs.appendFileSync(HEARTBEAT, `[${timestamp}] CRITICAL: Unidentified node detected on Wi-Fi: ${ip} (${mac}). Initiating active monitoring.\n`);
                    } else {
                        fs.appendFileSync(HEARTBEAT, `[${timestamp}] AUTH: ${deviceName} connected to grid.\n`);
                    }
                    
                    console.log(msg.trim());
                }
            }
        });
    });
}

console.log('[SPECTER] WiFi Sentinel active. Monitoring network traffic...');
setInterval(scanNetwork, 30000); // Scan every 30 seconds
scanNetwork();
