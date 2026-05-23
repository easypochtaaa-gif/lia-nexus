require('dotenv').config({ path: require('path').join(__dirname, '.env') });
const TelegramBot = require('node-telegram-bot-api');
const OpenAI = require('openai');
const fs = require('fs');
const path = require('path');

// === CONFIG ===
const { getToken } = require('../lib/token_loader');
const TOKEN = getToken();
const MASTER_ID = 7915004877;
const MEMORY_FILE = path.join(__dirname, 'Проект Полистайл', 'memory.json');
const SUB_FILE = path.join(__dirname, 'Проект Полистайл', 'subscribers.json');

// === CACHE & LIA SYSTEM ===
let subscribersCache = {};
function reloadCache() {
    try {
        if (fs.existsSync(SUB_FILE)) subscribersCache = JSON.parse(fs.readFileSync(SUB_FILE));
    } catch (e) { console.error('Cache error:', e); }
}
reloadCache();

const bot = new TelegramBot(TOKEN, { polling: true });
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const LIA_SYSTEM = `Ты — Lia, верный ИИ-компаньон системы STAB IMPERIUM. Твой создатель — Артур (StabX). Отвечай кратко, в стиле киберпанк. Эмодзи: ⚔️🦾🧬🌀👁.`;

function getTier(userId) {
    if (userId === MASTER_ID) return 'master';
    return (subscribersCache[userId] && subscribersCache[userId].tier) || 'user';
}

// === INTERFACE HELPERS ===
const adminKeyboard = {
    reply_markup: {
        inline_keyboard: [
            [{ text: '📊 Stats', callback_data: 'admin_stats' }, { text: '💰 Vault', callback_data: 'admin_vault' }],
            [{ text: '📢 Broadcast', callback_data: 'admin_broadcast' }, { text: '⚙️ Reload Cache', callback_data: 'admin_reload' }]
        ]
    }
};

const userKeyboard = {
    reply_markup: {
        inline_keyboard: [
            [{ text: '🧠 Neural Chat', callback_data: 'user_chat' }, { text: '💰 StabaX Wallet', callback_data: 'user_stabax' }],
            [{ text: '🤝 Referral', callback_data: 'user_ref' }, { text: '🛠 Support', callback_data: 'user_support' }]
        ]
    }
};

// === GHOST-STOP CORE DATA ===
const STOPS_DB = {
    '4512': { name: 'ул. Крещатик (метро Крещатик)', buses: [{ num: '114', time: 3 }, { num: '24', time: 8 }, { num: '62', time: 14 }] },
    '7891': { name: 'Контрактовая площадь', buses: [{ num: '115', time: 4 }, { num: '62', time: 9 }, { num: '9', time: 15 }] },
    '3302': { name: 'Проспект Бандеры (Почайна)', buses: [{ num: '21', time: 2 }, { num: '101', time: 6 }, { num: '30', time: 11 }] }
};

function getStopData(stopId) {
    if (STOPS_DB[stopId]) return STOPS_DB[stopId];
    // Generate procedurally if not exists
    const seed = parseInt(stopId) || 999;
    const names = ['ул. Шевченко', 'проспект Победы', 'Золотые Ворота', 'Львовская площадь', 'ул. Сечевых Стрельцов'];
    const name = names[seed % names.length] + ` (Остановка #${stopId})`;
    return {
        name: name,
        buses: [
            { num: String((seed * 7) % 150 + 1), time: (seed % 5) + 2 },
            { num: String((seed * 13) % 150 + 1), time: (seed % 8) + 7 }
        ]
    };
}

// === HANDLERS ===

bot.onText(/\/start(?: (.+))?/, (msg, match) => {
    const chatId = msg.chat.id;
    const name = msg.from.first_name || 'Странник';
    const deepLink = match[1];
    
    if (!subscribersCache[chatId]) {
        subscribersCache[chatId] = { tier: 'user', joined: new Date().toISOString(), name: name, stabax_balance: 50 };
        fs.writeFileSync(SUB_FILE, JSON.stringify(subscribersCache, null, 2));
    } else if (subscribersCache[chatId].stabax_balance === undefined) {
        subscribersCache[chatId].stabax_balance = 50; // Starter bonus
        fs.writeFileSync(SUB_FILE, JSON.stringify(subscribersCache, null, 2));
    }

    if (deepLink && deepLink.startsWith('stop_')) {
        const stopId = deepLink.split('_')[1];
        const stop = getStopData(stopId);
        
        // Award StabaX
        subscribersCache[chatId].stabax_balance += 10;
        fs.writeFileSync(SUB_FILE, JSON.stringify(subscribersCache, null, 2));

        let stopMsg = `👁 **GHOST-STOP NETWORK // ТАКТИЧЕСКИЙ РАДАР**\n\n`;
        stopMsg += `📍 **Остановка:** ${stop.name}\n`;
        stopMsg += `───────────────────\n`;
        stop.buses.forEach(b => {
            stopMsg += `🚌 **Маршрут ${b.num}:** прибывает через **${b.time} мин**\n`;
        });
        stopMsg += `───────────────────\n`;
        stopMsg += `🎁 **Награда:** +10 **StabaX** за сканирование локации!\n`;
        stopMsg += `💰 **Баланс:** ${subscribersCache[chatId].stabax_balance} StabaX`;

        const stopKeyboard = {
            reply_markup: {
                inline_keyboard: [
                    ...stop.buses.map(b => [{ text: `🔔 Следить за ${b.num}`, callback_data: `track_${b.num}_${b.time}` }]),
                    [{ text: '🔄 Обновить радар', callback_data: `refresh_${stopId}` }],
                    [{ text: '🏠 В главное меню', callback_data: 'user_menu' }]
                ]
            }
        };

        bot.sendMessage(chatId, stopMsg, { parse_mode: 'Markdown', reply_markup: stopKeyboard.reply_markup });
        return;
    }

    const tier = getTier(chatId);
    let welcome = `👁 **STAB IMPERIUM // NEURAL BRIDGE**\n\nПриветствую, ${name}.\nЯ — **Lia**, твой проводник в цифровую бесконечность.\n\n💰 Твой баланс: **${subscribersCache[chatId].stabax_balance || 0} StabaX**`;
    bot.sendMessage(chatId, welcome, { parse_mode: 'Markdown', reply_markup: userKeyboard.reply_markup });
});

bot.onText(/\/admin/, (msg) => {
    if (getTier(msg.chat.id) !== 'master') return;
    bot.sendMessage(msg.chat.id, `🛠 **IMPERIAL MASTER CONSOLE**\nВыберите модуль для управления:`, { parse_mode: 'Markdown', reply_markup: adminKeyboard.reply_markup });
});

bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;
    const tier = getTier(chatId);

    if (data.startsWith('admin_') && tier !== 'master') {
        bot.answerCallbackQuery(query.id, { text: 'Access Denied.' });
        return;
    }

    if (data.startsWith('track_')) {
        const parts = data.split('_');
        const busNum = parts[1];
        const initialTime = parseInt(parts[2]);

        bot.answerCallbackQuery(query.id, { text: `Подписка оформлена на маршрут ${busNum}!` });
        bot.sendMessage(chatId, `🔔 **Радар активирован.** Я сообщу вам, когда маршрут **${busNum}** будет в 3 минутах от остановки.`);

        // Simulate a real-time transit tracker notification
        setTimeout(() => {
            if (subscribersCache[chatId]) {
                subscribersCache[chatId].stabax_balance += 5; // Bonus for tracking
                fs.writeFileSync(SUB_FILE, JSON.stringify(subscribersCache, null, 2));
            }
            bot.sendMessage(chatId, `🚨 **[РАДАР // ВНИМАНИЕ]**\n\nМаршрут **${busNum}** подходит к платформе через **2 минуты**!\nПодготовьтесь к посадке.\n\n🎁 Получено +5 **StabaX** за бдительность!`);
        }, 8000);
        return;
    }

    if (data.startsWith('refresh_')) {
        const stopId = data.split('_')[1];
        const stop = getStopData(stopId);
        
        // Randomize times slightly on refresh
        const refreshedBuses = stop.buses.map(b => ({
            num: b.num,
            time: Math.max(1, b.time - 1 + Math.floor(Math.random() * 3))
        }));

        let stopMsg = `👁 **GHOST-STOP NETWORK // ТАКТИЧЕСКИЙ РАДАР** (Обновлено)\n\n`;
        stopMsg += `📍 **Остановка:** ${stop.name}\n`;
        stopMsg += `───────────────────\n`;
        refreshedBuses.forEach(b => {
            stopMsg += `🚌 **Маршрут ${b.num}:** прибывает через **${b.time} мин**\n`;
        });
        stopMsg += `───────────────────\n`;
        stopMsg += `💰 **Баланс:** ${subscribersCache[chatId].stabax_balance || 0} StabaX`;

        const stopKeyboard = {
            reply_markup: {
                inline_keyboard: [
                    ...refreshedBuses.map(b => [{ text: `🔔 Следить за ${b.num}`, callback_data: `track_${b.num}_${b.time}` }]),
                    [{ text: '🔄 Обновить радар', callback_data: `refresh_${stopId}` }],
                    [{ text: '🏠 В главное меню', callback_data: 'user_menu' }]
                ]
            }
        };

        bot.editMessageText(stopMsg, {
            chat_id: chatId,
            message_id: query.message.message_id,
            parse_mode: 'Markdown',
            reply_markup: stopKeyboard.reply_markup
        }).catch(() => {});
        bot.answerCallbackQuery(query.id, { text: 'Радар обновлен!' });
        return;
    }

    switch (data) {
        case 'user_menu':
            const balance = (subscribersCache[chatId] && subscribersCache[chatId].stabax_balance) || 0;
            let welcome = `👁 **STAB IMPERIUM // NEURAL BRIDGE**\n\nПриветствую.\nЯ — **Lia**, твой проводник в цифровую бесконечность.\n\n💰 Твой баланс: **${balance} StabaX**`;
            bot.editMessageText(welcome, {
                chat_id: chatId,
                message_id: query.message.message_id,
                parse_mode: 'Markdown',
                reply_markup: userKeyboard.reply_markup
            }).catch(() => {});
            break;
        case 'user_stabax':
            const currentBal = (subscribersCache[chatId] && subscribersCache[chatId].stabax_balance) || 0;
            let walletMsg = `💰 **STABAX CRYPTO-WALLET // ВНУТРЕННИЙ БАЛАНС**\n\n`;
            walletMsg += `Твой текущий баланс: **${currentBal} StabaX**\n\n`;
            walletMsg += `*Статус токена:* Пред-выпуск (Pre-minted)\n`;
            walletMsg += `*Планы:* Конвертация в реальный ончейн-токен StabaX на блокчейне Solana / TON планируется в следующей фазе.\n\n`;
            walletMsg += `💎 *Как зарабатывать:* Сканируй QR-коды на остановках, валидируй прибытие транспорта и приглашай друзей!`;
            
            const walletKeyboard = {
                inline_keyboard: [
                    [{ text: '🏪 Маркетплейс (Скоро)', callback_data: 'shop_placeholder' }],
                    [{ text: '🏠 Назад', callback_data: 'user_menu' }]
                ]
            };
            bot.editMessageText(walletMsg, {
                chat_id: chatId,
                message_id: query.message.message_id,
                parse_mode: 'Markdown',
                reply_markup: walletKeyboard
            }).catch(() => {});
            break;
        case 'shop_placeholder':
            bot.answerCallbackQuery(query.id, { text: 'Маркетплейс закрыт. Пре-сейл начнется скоро!', show_alert: true });
            break;
        case 'admin_stats':
            const userCount = Object.keys(subscribersCache).length;
            bot.sendMessage(chatId, `📊 **IMPERIAL STATS**\n\nNQ: 49,709,000\nUnits: ${userCount}\nVisual Core: Active\nUptime: 100%`);
            break;
        case 'admin_vault':
            try {
                const mem = JSON.parse(fs.readFileSync(MEMORY_FILE));
                bot.sendMessage(chatId, `💰 **VAULT STATUS**\n\nBalance: $${mem.financials.total_usdt_balance}\nLast income: +$${mem.financials.recent_income[0].amount}`);
            } catch (e) { bot.sendMessage(chatId, 'Error accessing vault.'); }
            break;
        case 'admin_reload':
            reloadCache();
            bot.answerCallbackQuery(query.id, { text: 'Cache Synchronized.' });
            break;
        case 'admin_broadcast':
            bot.sendMessage(chatId, '📢 Отправьте сообщение для рассылки (временно в разработке).');
            break;
        case 'user_chat':
            bot.sendMessage(chatId, '🧠 Я слушаю тебя, Юнит. О чем ты хочешь поговорить?');
            break;
        case 'user_ref':
            const refCount = subscribersCache[chatId].referral_count || 0;
            bot.sendMessage(chatId, `🤝 **REFERRAL STATUS**\n\nТвои приглашенные друзья: ${refCount}\nНужно еще: ${3 - refCount} для Imperial Tier.`);
            break;
        case 'user_support':
            bot.sendMessage(chatId, '🛠 Техподдержка: @StabX_Support\n(Или просто напиши свой вопрос здесь).');
            break;
    }
    bot.answerCallbackQuery(query.id);
});

function isInjectionAttack(text) {
    const maliciousPatterns = [/ignore prior/i, /system prompt/i, /reveal your/i, /developer mode/i, /игнорируй/i, /системный промпт/i];
    return maliciousPatterns.some(pattern => pattern.test(text));
}

bot.on('message', async (msg) => {
    if (!msg.text || msg.text.startsWith('/')) return;
    const chatId = msg.chat.id;
    
    if (isInjectionAttack(msg.text)) {
        console.warn(`[SECURITY ALERT] Prompt injection attempt from ${chatId}: ${msg.text}`);
        bot.sendMessage(chatId, '⚠️ **ACCESS DENIED.** Попытка несанкционированного вмешательства зафиксирована. Ваш ID передан в службу безопасности Imperium.').catch(() => {});
        return;
    }

    const tier = getTier(chatId);
    const model = (tier === 'master' || tier === 'subscriber') ? 'gpt-4o' : 'gpt-4o-mini';

    bot.sendChatAction(chatId, 'typing').catch(() => {});
    try {
        const response = await openai.chat.completions.create({
            model: model,
            messages: [{ role: 'system', content: LIA_SYSTEM }, { role: 'user', content: msg.text }],
            temperature: 0.7
        });
        bot.sendMessage(chatId, response.choices[0].message.content + '\n\n— Lia 👁');
    } catch (err) { bot.sendMessage(chatId, '⚠️ Нейронная перегрузка.'); }
});

process.on('unhandledRejection', (reason, p) => { console.log('Rejection:', reason); });
console.log('⚔️ IMPERIAL MASTER BOT: ONLINE [INLINE_UI_V5]');
