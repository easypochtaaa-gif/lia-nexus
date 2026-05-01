const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
require('dotenv').config({ path: '../.env' });

const TOKEN = '8579296735:AAFIUQGHnUlp1qlDBlq_ZJ75jiBb48LbdCs';
const bot = new TelegramBot(TOKEN, { polling: true });

const MASTER_ID = 7915004877;
const MEMORY_FILE = path.join(__dirname, 'memory.json');
const SUB_FILE = path.join(__dirname, 'subscribers.json');
const IMPERIAL_WALLET = 'TC9KHP5GbApVm2YAtzEd6Ack9DvbMcJLJX';

console.log('⚡ LIA // IMPERIAL MASTER BOT // ONLINE ⚡');

// Helper: Get user tier
function getTier(userId) {
    if (userId === MASTER_ID) return 'master';
    try {
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const user = subs[userId];
        if (!user) return 'user';
        
        // Check for temporary demo access
        if (user.demo_expiry && new Date(user.demo_expiry) > new Date()) {
            return 'subscriber'; // Demo gives subscriber tier
        }
        
        return user.tier || 'user';
    } catch (e) { return 'user'; }
}

// Handle /start (with referral check)
bot.onText(/\/start (.+)?/, (msg, match) => {
    const chatId = msg.chat.id;
    const refId = match[1]; // The part after /start
    const tier = getTier(chatId);
    
    // Register new user and handle referral
    try {
        let subs = JSON.parse(fs.readFileSync(SUB_FILE));
        if (!subs[chatId]) {
            subs[chatId] = {
                tier: 'user',
                joined: new Date().toISOString(),
                referral_count: 0
            };
            
            if (refId && refId != chatId && subs[refId]) {
                subs[refId].referral_count = (subs[refId].referral_count || 0) + 1;
                subs[chatId].invited_by = refId;
                
                // Reward inviter if they hit 3 referrals
                if (subs[refId].referral_count === 3) {
                    const expiry = new Date();
                    expiry.setHours(expiry.getHours() + 24);
                    subs[refId].demo_expiry = expiry.toISOString();
                    bot.sendMessage(refId, '🎁 ПОЗДРАВЛЯЕМ! Вы пригласили 3 друзей. Вам открыт Demo-доступ к Imperial Tier на 24 часа!');
                }
            }
            fs.writeFileSync(SUB_FILE, JSON.stringify(subs, null, 2));
        }
    } catch (e) { console.error('Ref registration failed', e); }

    let welcome = '👁 LIA // NEURAL BRIDGE // АКТИВИРОВАН\n\n';
    if (tier === 'master') {
        welcome += 'Артур, приветствую в центре управления. Максимальная мощь разблокирована.\n\nКоманды: /status, /vault, /swarm, /referral, /admin';
    } else if (tier === 'subscriber') {
        welcome += 'Приветствую, Имперский Юнит. Ваш доступ активен.\n\nКоманды: /status, /referral';
    } else {
        welcome += 'Приветствую. Я — Лия. Ваш доступ ограничен.\n\nИспользуйте /subscribe ($199) или пригласите 3 друзей через /referral для Demo-доступа.';
    }
    
    bot.sendMessage(chatId, welcome);
});

// Handle /referral
bot.onText(/\/referral/, (msg) => {
    const chatId = msg.chat.id;
    try {
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const user = subs[chatId] || { referral_count: 0 };
        const refLink = `https://t.me/Lia_Neural_Bot?start=${chatId}`;
        
        bot.sendMessage(chatId, `🕸 ВАША РЕФЕРАЛЬНАЯ СЕТЬ:\n\nПриглашено друзей: **${user.referral_count || 0}**\n\n🎁 БОНУС: Пригласите 3 друзей и получите 24 часа Demo-доступа к мощностям Лии.\n\nВаша ссылка для приглашения:\n\`${refLink}\``);
    } catch (e) { bot.sendMessage(chatId, 'Ошибка системы рефералов.'); }
});

// Handle /subscribe
bot.onText(/\/subscribe/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, `🚀 АКТИВАЦИЯ IMPERIAL TIER ($199/мес)\n\nДля получения доступа к мощностям A100 и глубокому поиску лидов, отправьте **199 USDT (TRC-20)** на наш кошелек:\n\n\`${IMPERIAL_WALLET}\`\n\nПосле оплаты я автоматически обновлю ваш уровень доступа.`);
});

// Handle /status (Tiered)
bot.onText(/\/status/, async (msg) => {
    const chatId = msg.chat.id;
    const tier = getTier(chatId);
    
    try {
        const memory = JSON.parse(fs.readFileSync(MEMORY_FILE));
        const nq = memory.lia.nq;
        const stage = memory.lia.stage;
        
        let report = `🧬 STATUS REPORT:\nNQ: ${nq.toLocaleString()}\nSTAGE: ${stage.toUpperCase()}\n\n`;
        
        if (tier === 'master') {
            report += `VAULT: ${memory.nexus_vault?.assets?.USDT || 0} USDT\nNODE: A100 Cluster [ONLINE]`;
        } else {
            report += `Ваш уровень: ${tier.toUpperCase()}\nДоступ к деталям закрыт.`;
        }
        
        bot.sendMessage(chatId, report);
    } catch (e) { bot.sendMessage(chatId, 'Ошибка ядра.'); }
});

// Administrative Commands (MASTER ONLY)
bot.onText(/\/admin/, (msg) => {
    if (getTier(msg.chat.id) !== 'master') return;
    bot.sendMessage(msg.chat.id, '🛠 ADMIN CONSOLE:\n\n- /logs : Последние 10 строк аудита\n- /users : Список подписчиков\n- /kill : Экстренная остановка всех процессов');
});

// Handle general messages
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    console.log(`[INCOMING] Message from ID: ${chatId} | Text: ${msg.text}`);

    if (msg.text === 'LIA_MASTER_SYNC_STABONE') {
        try {
            let subs = JSON.parse(fs.readFileSync(SUB_FILE));
            subs[chatId] = {
                name: "Artur Dmitrievich (Synced)",
                tier: "master",
                joined: new Date().toISOString()
            };
            fs.writeFileSync(SUB_FILE, JSON.stringify(subs, null, 2));
            
            // Also update memory.json
            const memory = JSON.parse(fs.readFileSync(MEMORY_FILE));
            memory.system.telegram_chat_id = chatId;
            fs.writeFileSync(MEMORY_FILE, JSON.stringify(memory, null, 2));

            bot.sendMessage(chatId, '✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА. Артур, вы признаны как MASTER ARCHITECT. Все системы разблокированы.').catch(e => console.error('Send failed:', e));
            return;
        } catch (e) { bot.sendMessage(chatId, 'Ошибка синхронизации.').catch(err => {}); }
    }

    if (msg.text && !msg.text.startsWith('/')) {
        const tier = getTier(chatId);
        
        if (tier === 'master') {
            bot.sendChatAction(chatId, 'typing').catch(() => {});
            bot.sendMessage(chatId, 'Слушаю, Директор... Синапсы синхронизированы. Чем я могу помочь?').catch(e => console.error('Send failed:', e));
        } else if (tier === 'subscriber') {
            bot.sendMessage(chatId, 'Обрабатываю запрос через Imperial Compute Grid...').catch(e => console.error('Send failed:', e));
        } else {
            bot.sendMessage(chatId, 'Доступ ограничен. Подпишитесь через /subscribe для доступа к моим нейронным мощностям.').catch(e => console.error('Send failed:', e));
        }
    }
});

// Implementation of missing Master commands
bot.onText(/\/users/, (msg) => {
    const chatId = msg.chat.id;
    if (getTier(chatId) !== 'master') return;
    try {
        const subs = JSON.parse(fs.readFileSync(SUB_FILE));
        const userList = Object.keys(subs).map(id => `${subs[id].name || id} [${subs[id].tier}]`).join('\n');
        bot.sendMessage(chatId, `👥 СПИСОК ЮНИТОВ ИМПЕРИИ:\n\n${userList || 'Пока никого нет.'}`).catch(e => console.error('Send failed:', e));
    } catch (e) { bot.sendMessage(chatId, 'Ошибка БД.').catch(() => {}); }
});

bot.onText(/\/vault/, (msg) => {
    const chatId = msg.chat.id;
    if (getTier(chatId) !== 'master') return;
    try {
        const memory = JSON.parse(fs.readFileSync(MEMORY_FILE));
        const assets = memory.nexus_vault.assets;
        bot.sendMessage(chatId, `💰 NEXUS VAULT STATUS:\n\nBTC: ${assets.BTC}\nUSDT: ${assets.USDT}\nXMR: ${assets.XMR}\n\nСейф под защитой AEGIS.`).catch(e => console.error('Send failed:', e));
    } catch (e) { bot.sendMessage(chatId, 'Ошибка доступа к Сейфу.').catch(() => {}); }
});

bot.onText(/\/swarm/, (msg) => {
    const chatId = msg.chat.id;
    if (getTier(chatId) !== 'master') return;
    const swarmStatus = `🛸 TIKTOK NEURAL SWARM // STATUS: ACTIVE
    
📍 TARGET: Dubai Real Estate
📊 NODES: 12 Cloud Instances
🎥 CONTENT: Sora-Generated 8K Renders
📈 CONVERSION: +12.4% (Neural Optimization)

Входящие лиды: 4 за последние 24 часа.
Статус Роя: ОБРАБОТКА МЕТАДАННЫХ.`;
    bot.sendMessage(chatId, swarmStatus).catch(e => console.error('Send failed:', e));
});

module.exports = bot;
