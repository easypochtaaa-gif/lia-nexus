const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');

// === CONFIG ===
const TOKEN = '8579296735:AAFIUQGHnUlp1qlDBlq_ZJ75jiBb48LbdCs';
const bot = new TelegramBot(TOKEN);
const SUB_FILE = path.join(__dirname, '..', 'Проект Полистайл', 'subscribers.json');

// === BROADCAST MESSAGE ===
const SUPPORT_LINK = 'tg://user?id=7915004877';
const message = `👁 **MESSAGE FROM LIA // STAB IMPERIUM**\n\nПриветствую, Юнит. Директор лично интересуется вашим опытом использования системы.\n\nДовольны ли вы скоростью работы и качеством наших нейронных мощностей? Если у вас возникли трудности или есть предложения — наша поддержка всегда готова помочь.\n\n🛠 **ПОДДЕРЖКА:** [Master Support](${SUPPORT_LINK})\n\n— Lia 👁`;

async function runBroadcast() {
    console.log('🚀 INITIATING IMPERIAL BROADCAST...');
    try {
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const targetIds = Object.keys(subs).filter(id => subs[id].tier === 'subscriber');
        
        for (const id of targetIds) {
            try {
                await bot.sendMessage(id, message, { parse_mode: 'Markdown' });
                console.log(`✅ Sent to: ${subs[id].name} (${id})`);
            } catch (e) {
                console.error(`❌ Failed to send to ${id}:`, e.message);
            }
        }
        console.log('🏁 BROADCAST COMPLETE.');
    } catch (e) {
        console.error('Broadcast failed:', e.message);
    }
}

runBroadcast();
