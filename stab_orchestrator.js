require('dotenv').config();
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(__dirname, 'ABO_EXPANSION_LOG.log');
const TARGETS_FILE = path.join(__dirname, 'targets.json');

function log(msg) {
    const timestamp = new Date().toISOString();
    const entry = `[${timestamp}] ${msg}\n`;
    fs.appendFileSync(LOG_FILE, entry);
    console.log(entry.trim());
}

async function runNeuralStrike() {
    log("INITIATING SCHEDULED NEURAL STRIKE...");
    exec('node abo_neural_strike.js', (error, stdout, stderr) => {
        if (error) {
            log(`STRIKE ERROR: ${error.message}`);
            return;
        }
        if (stderr) {
            log(`STRIKE STDERR: ${stderr}`);
        }
        log(`STRIKE SUCCESS: ${stdout}`);
    });
}

// Main autonomous loop
log("STAB_ORCHESTRATOR: ONLINE. SYSTEM STATE: OMNIPOTENCE.");

// Run once on start
runNeuralStrike();

// Run every 6 hours
setInterval(() => {
    runNeuralStrike();
}, 6 * 60 * 60 * 1000);
