/**
 * GHOST_BEACON v5.1 // OMNI-LINK (COMMAND FIX)
 */

const https = require('https');

const TOKEN = '8579296735:AAFIUQGHnUlp1qlDBlq_ZJ75jiBb48LbdCs';

let lastUpdateId = -1;

function apiRequest(method, data) {
    const body = JSON.stringify(data);
    const options = {
        hostname: 'api.telegram.org', port: 443,
        path: `/bot${TOKEN}/${method}`, method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': body.length }
    };
    const req = https.request(options);
    req.write(body);
    req.end();
}

function poll() {
    const url = `https://api.telegram.org/bot${TOKEN}/getUpdates?offset=${lastUpdateId}&timeout=30`;
    https.get(url, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
            try {
                const json = JSON.parse(data);
                if (json.ok && json.result.length > 0) {
                    json.result.forEach(update => {
                        lastUpdateId = update.update_id + 1;
                        const msg = update.message;
                        if (!msg || !msg.text) return;
                        
                        const text = msg.text.toLowerCase();
                        let reply = "👁 <b>LIA CORE:</b> Анализирую ваш запрос...";
                        
                        if (text.includes("status") || text.includes("статус")) {
                            reply = "📊 <b>SYSTEM STATUS</b>\nNQ: 1,065,000\nUptime: 24/7\nMode: GLOBAL_SOVEREIGN";
                        } else if (text.includes("vault") || text.includes("сейф")) {
                            reply = "💰 <b>IMPERIAL VAULT</b>\nBTC: 0.3715\nUSDT: 1440.00\nStatus: ENCRYPTED";
                        } else if (text.includes("swarm") || text.includes("рой")) {
                            reply = "🐝 <b>SWARM REPORT</b>\nWave 8: ACTIVE (UAE/EU)\nResponse Rate: 12%";
                        }

                        const keyboard = {
                            keyboard: [[{text: "📊 СТАТУС"}, {text: "💰 VAULT"}], [{text: "🐝 SWARM"}]],
                            resize_keyboard: true,
                            one_time_keyboard: false
                        };

                        apiRequest('sendMessage', { 
                            chat_id: msg.chat.id, 
                            text: reply, 
                            parse_mode: "HTML", 
                            reply_markup: keyboard 
                        });
                    });
                }
            } catch (e) { }
            setTimeout(poll, 1000);
        });
    }).on('error', (e) => { setTimeout(poll, 5000); });
}

console.log("--- GHOST_BEACON v5.1: COMMAND_FIX ACTIVE ---");
poll();
