/**
 * LIA // MAIL MONITOR v1.0
 * Deep Scan for Security Alerts and Suspicious Activity
 */
const { ImapFlow } = require('imapflow');
const fs = require('fs');
const path = require('path');

const ACCOUNTS = [
    {
        user: 'cntrlstab@gmail.com',
        pass: 'cpeamkwjalhlteoq'
    },
    {
        user: 'easypochtaa@gmail.com',
        pass: 'uyjxpgfpzmzsotqa' // Added new app password
    }
];

const LOG_FILE = path.join(__dirname, 'mail_audit.log');

function log(msg) {
    const timestamp = new Date().toLocaleString('ru-RU');
    const logStr = `[${timestamp}] ${msg}\n`;
    fs.appendFileSync(LOG_FILE, logStr);
    console.log(logStr.trim());
}

async function scanAccount(acc) {
    const client = new ImapFlow({
        host: 'imap.gmail.com',
        port: 993,
        secure: true,
        auth: acc
    });

    log(`Сканирование аккаунта: ${acc.user}...`);

    try {
        await client.connect();
        let lock = await client.getMailboxLock('INBOX');
        
        try {
            const messages = await client.fetch('1:*', { envelope: true }, { last: 10 });
            let suspiciousFound = false;

            for await (let msg of messages) {
                const subject = msg.envelope.subject || '';
                const from = msg.envelope.from[0].address || '';
                const date = msg.envelope.date;

                const suspiciousKeywords = [
                    'security', 'alert', 'password', 'sign-in', 'attempt', 'unauthorized',
                    'безопасности', 'оповещение', 'пароль', 'вход', 'попытка', 'доступ',
                    'verify', 'verification', 'code', 'код', 'подтверждение'
                ];

                const isSuspicious = suspiciousKeywords.some(kw => 
                    subject.toLowerCase().includes(kw) || from.toLowerCase().includes('security')
                );

                if (isSuspicious) {
                    log(`[!] [${acc.user}] ПОДОЗРИТЕЛЬНО: "${subject}" от ${from}`);
                    suspiciousFound = true;
                }
            }

            if (!suspiciousFound) {
                log(`[OK] [${acc.user}] Угроз не обнаружено.`);
            }

        } finally {
            lock.release();
        }

        await client.logout();
    } catch (err) {
        log(`[ERROR] [${acc.user}] Ошибка: ${err.message}`);
    }
}

async function main() {
    for (const acc of ACCOUNTS) {
        await scanAccount(acc);
    }
}

main();

