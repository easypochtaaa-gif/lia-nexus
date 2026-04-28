const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const LOG_FILE = 'security_audit.log';
const SCAN_INTERVAL = 30000; // 30 seconds
const ADB_PATH = path.join(__dirname, 'platform-tools', 'adb.exe');

let lastCellIds = {
    vodafone: null,
    kyivstar: null
};

function log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    console.log(logMessage.trim());
    fs.appendFileSync(path.join(__dirname, LOG_FILE), logMessage);
}

function scanSecurity() {
    try {
        // 1. Cell ID Monitor
        const telephony = execSync(`"${ADB_PATH}" shell dumpsys telephony.registry`).toString();
        const cells = telephony.match(/mCi=\d+/g);
        
        if (cells) {
            const currentIds = {
                vodafone: cells[0] ? cells[0].split('=')[1] : null,
                kyivstar: cells[1] ? cells[1].split('=')[1] : null
            };

            if (lastCellIds.vodafone && currentIds.vodafone !== lastCellIds.vodafone) {
                log(`⚠️ ALERT: Vodafone Cell ID changed! ${lastCellIds.vodafone} -> ${currentIds.vodafone}`);
            }
            if (lastCellIds.kyivstar && currentIds.kyivstar !== lastCellIds.kyivstar) {
                log(`⚠️ ALERT: Kyivstar Cell ID changed! ${lastCellIds.kyivstar} -> ${currentIds.kyivstar}`);
            }

            lastCellIds = currentIds;
        }

        // 2. Wi-Fi Monitor (check for new hidden SSIDs)
        const wifi = execSync(`"${ADB_PATH}" shell cmd wifi list-scan-results`).toString();
        if (wifi.includes('MiShareWiFi')) {
            log('ℹ️ INFO: MiShare activity detected in vicinity.');
        }

    } catch (error) {
        log(`❌ ERROR: Monitor failed - ${error.message}`);
    }
}

log('🚀 LIA SECURITY MONITOR STARTED. Monitoring Cell IDs and Wi-Fi environment...');
setInterval(scanSecurity, SCAN_INTERVAL);
scanSecurity();
