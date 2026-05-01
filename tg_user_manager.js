const { TelegramClient } = require('telegram');
const { StringSession } = require('telegram/sessions');
const input = require('input');
const fs = require('fs');
const path = require('path');

const SESSION_DIR = path.join(__dirname, 'sessions');
if (!fs.existsSync(SESSION_DIR)) fs.mkdirSync(SESSION_DIR);

class TGUserManager {
    constructor() {
        this.clients = {};
    }

    async initClient(phoneNumber, apiId, apiHash) {
        const sessionPath = path.join(SESSION_DIR, `${phoneNumber}.session`);
        let stringSession = '';
        if (fs.existsSync(sessionPath)) {
            stringSession = fs.readFileSync(sessionPath, 'utf8');
        }
        const client = new TelegramClient(new StringSession(stringSession), apiId, apiHash, { connectionRetries: 5 });
        await client.connect();
        return client;
    }

    async saveSession(phoneNumber, client) {
        const sessionPath = path.join(SESSION_DIR, `${phoneNumber}.session`);
        fs.writeFileSync(sessionPath, client.session.save(), 'utf8');
        this.clients[phoneNumber] = client;
    }

    getActiveSessions() {
        return Object.keys(this.clients).map(phone => ({ phone }));
    }

    async broadcast(message) {
        for (const phone in this.clients) {
            const client = this.clients[phone];
            await client.sendMessage('me', { message: `[SYSTEM_REPORT] ${message}` });
        }
    }
}

module.exports = new TGUserManager();
