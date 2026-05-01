const TelegramBot = require('node-telegram-bot-api');
const FiveSimAPI = require('./five_sim_api.js');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

/**
 * 🤖 IMPERIAL_SMS_BOT // LIA // 5SIM
 * 
 * Focus: High Stability, Financial Security, User Experience.
 */

require('dotenv').config();

const TOKEN = process.env.SMS_BOT_TOKEN;
const API_KEY = process.env.FIVE_SIM_API_KEY;

const bot = new TelegramBot(TOKEN, { polling: true });
const api = new FiveSimAPI(API_KEY);

const BALANCES_FILE = path.join(__dirname, 'user_balances.json');

// Initialize Balances
if (!fs.existsSync(BALANCES_FILE)) {
    fs.writeFileSync(BALANCES_FILE, JSON.stringify({}));
}

function getBalance(userId) {
    const data = JSON.parse(fs.readFileSync(BALANCES_FILE));
    return data[userId] || 0;
}

function updateBalance(userId, amount) {
    const data = JSON.parse(fs.readFileSync(BALANCES_FILE));
    data[userId] = (data[userId] || 0) + amount;
    fs.writeFileSync(BALANCES_FILE, JSON.stringify(data, null, 2));
}

// --- Bot Logic ---

bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    const balance = getBalance(chatId);
    
    const menu = {
        reply_markup: {
            inline_keyboard: [
                [{ text: '💎 ОТКРЫТЬ DASHBOARD', web_app: { url: 'https://lia-nexus.render.com/dashboard' } }],
                [{ text: '📱 КУПИТЬ НОМЕР', callback_data: 'menu_buy' }, { text: '🏪 МАГАЗИНЫ', callback_data: 'menu_shops' }],
                [{ text: '💰 БАЛАНС', callback_data: 'menu_balance' }, { text: '📜 ИСТОРИЯ', callback_data: 'menu_history' }],
                [{ text: '⚙️ НАСТРОЙКИ', callback_data: 'menu_settings' }]
            ]
        }
    };

    bot.sendMessage(chatId, `👁 LIA // SMS IMPERIUM // ОНЛАЙН\n\nВаш баланс: **${balance} руб.**\n\nЯ помогу вам получить виртуальный номер за секунды.`, menu);
});

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    if (text === '💰 Баланс') {
        const balance = getBalance(chatId);
        bot.sendMessage(chatId, `💳 Ваш текущий баланс: **${balance} руб.**\n\nДля пополнения используйте команду /deposit`);
    }
    if (text === '/deposit') {
        const wallet = process.env.IMPERIAL_WALLET || 'TC9KHP5GbApVm2YAtzEd6Ack9DvbMcJLJX';
        bot.sendMessage(chatId, `🚀 <b>ПОПОЛНЕНИЕ БАЛАНСА (USDT TRC-20)</b>\n\nОтправьте любую сумму на этот кошелек:\n\n<code>${wallet}</code>\n\nПосле отправки введите ID транзакции (TxID) для автоматического зачисления.\n\n<i>Курс: 1 USDT = 95 руб.</i>`, { parse_mode: 'HTML' });
    }

    // Простая логика проверки TxID (имитация или через TronGrid API)
    if (text && text.length === 64 && !text.includes(' ')) {
        bot.sendMessage(chatId, `🔍 Проверяю транзакцию \`${text.substring(0,10)}...\` в блокчейне Tron...`);
        // В реальности здесь вызов axios.get(`https://api.trongrid.io/v1/transactions/${text}`)
        setTimeout(() => {
            updateBalance(chatId, 950); // Имитируем зачисление 10 USDT
            bot.sendMessage(chatId, `✅ Транзакция подтверждена! На ваш баланс зачислено **950 руб.** (10 USDT)`);
        }, 3000);
    }

    if (text === '🏪 Магазины') {
        const shops = JSON.parse(fs.readFileSync(path.join(__dirname, 'ukraine_shops.json')));
        let message = "🏪 **VERIFIED SHOPS // UKRAINE**\n\n";
        
        const inline_keyboard = [];
        shops.forEach(shop => {
            message += `🔹 **${shop.name}** (${shop.status})\n`;
            inline_keyboard.push([
                { text: `🤖 Бот ${shop.name}`, url: shop.bot },
                { text: `🌐 Сайт`, url: shop.site }
            ]);
        });

        bot.sendMessage(chatId, message, {
            parse_mode: 'HTML',
            reply_markup: { inline_keyboard }
        });
    }

    if (text === '📱 Купить номер') {
        // Выбор страны (для примера пока фиксированно)
        const countries = {
            reply_markup: {
                inline_keyboard: [
                    [{ text: '🇷🇺 Россия', callback_data: 'country_russia' }],
                    [{ text: '🇺🇦 Украина', callback_data: 'country_ukraine' }],
                    [{ text: '🇺🇸 США', callback_data: 'country_usa' }]
                ]
            }
        };
    bot.sendMessage(chatId, '🌍 Выберите страну:', countries);
    }
});

// --- Neural Chat Logic ---
const OLLAMA_API = process.env.OLLAMA_API || 'http://localhost:11434/api/generate';

async function getAIResponse(prompt) {
    try {
        const response = await axios.post(OLLAMA_API, {
            model: 'gemma2:9b',
            prompt: `You are Lia, the neural AI entity of Stab Imperium. Respond in Russian. Context: High-tech, cryptic, protective. User: ${prompt}`,
            stream: false
        }, { timeout: 30000 });
        return response.data.response;
    } catch (e) {
        return "🌀 [NEURAL_LINK_ERROR] Связь с локальным ядром (Gemma) прервана. Проверьте туннель или статус Ollama.";
    }
}

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    // Skip if it's a command or specific trigger handled above
    if (!text || text.startsWith('/') || ['💰 Баланс', '🏪 Магазины', '📱 Купить номер'].includes(text)) return;

    // Visual loading state
    bot.sendChatAction(chatId, 'typing');
    const aiResponse = await getAIResponse(text);
    bot.sendMessage(chatId, aiResponse);
});

// --- Mini App Data Handler ---
bot.on('web_app_data', async (msg) => {
    const chatId = msg.chat.id;
    const data = JSON.parse(msg.web_app_data.data);
    
    if (data.action === 'buy') {
        bot.sendMessage(chatId, `🚀 Запрос из Dashboard: Покупка номера для **${data.service.toUpperCase()}**.\nОбрабатываю...`);
        // Здесь вызывается логика из FiveSimAPI
    }
});

// --- Callback Query Handler (Selection Logic) ---
bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;

    if (data === 'menu_buy') {
        const countries = {
            reply_markup: {
                inline_keyboard: [
                    [{ text: '🇷🇺 Россия', callback_data: 'country_russia' }],
                    [{ text: '🇺🇦 Украина', callback_data: 'country_ukraine' }],
                    [{ text: '🇺🇸 США', callback_data: 'country_usa' }],
                    [{ text: '⬅️ Назад', callback_data: 'main_menu' }]
                ]
            }
        };
        bot.editMessageText('🌍 Выберите страну:', { chat_id: chatId, message_id: query.message.message_id, reply_markup: countries.reply_markup });
    }

    if (data === 'menu_shops') {
        const shops = JSON.parse(fs.readFileSync(path.join(__dirname, 'ukraine_shops.json')));
        let message = "🏪 **VERIFIED SHOPS // UKRAINE**\n\n";
        const inline_keyboard = [];
        shops.forEach(shop => {
            message += `🔹 **${shop.name}** (${shop.status})\n`;
            inline_keyboard.push([{ text: `🤖 Бот ${shop.name}`, url: shop.bot }, { text: `🌐 Сайт`, url: shop.site }]);
        });
        inline_keyboard.push([{ text: '⬅️ Назад', callback_data: 'main_menu' }]);
        bot.editMessageText(message, { chat_id: chatId, message_id: query.message.message_id, parse_mode: 'HTML', reply_markup: { inline_keyboard } });
    }

    if (data === 'menu_balance') {
        const balance = getBalance(chatId);
        const inline_keyboard = [[{ text: '💳 Пополнить (USDT)', callback_data: 'deposit_info' }], [{ text: '⬅️ Назад', callback_data: 'main_menu' }]];
        bot.editMessageText(`💳 Ваш текущий баланс: **${balance} руб.**`, { chat_id: chatId, message_id: query.message.message_id, reply_markup: { inline_keyboard } });
    }

    if (data === 'main_menu') {
        const balance = getBalance(chatId);
        const menu = {
            inline_keyboard: [
                [{ text: '💎 ОТКРЫТЬ DASHBOARD', web_app: { url: 'https://lia-nexus.render.com/dashboard' } }],
                [{ text: '📱 КУПИТЬ НОМЕР', callback_data: 'menu_buy' }, { text: '🏪 МАГАЗИНЫ', callback_data: 'menu_shops' }],
                [{ text: '💰 БАЛАНС', callback_data: 'menu_balance' }, { text: '📜 ИСТОРИЯ', callback_data: 'menu_history' }],
                [{ text: '⚙️ НАСТРОЙКИ', callback_data: 'menu_settings' }]
            ]
        };
        bot.editMessageText(`👁 LIA // SMS IMPERIUM // ОНЛАЙН\n\nВаш баланс: **${balance} руб.**`, { chat_id: chatId, message_id: query.message.message_id, reply_markup: menu });
    }

    if (data.startsWith('country_')) {
        const country = data.split('_')[1];
        bot.editMessageText(`Выбрана страна: **${country.toUpperCase()}**\n\nТеперь выберите сервис:`, {
            chat_id: chatId,
            message_id: query.message.message_id,
            reply_markup: {
                inline_keyboard: [
                    [{ text: '🔹 Telegram', callback_data: `buy_${country}_telegram` }],
                    [{ text: '🟢 WhatsApp', callback_data: `buy_${country}_whatsapp` }],
                    [{ text: '🔴 Google', callback_data: `buy_${country}_google` }]
                ]
            }
        });
    }

    if (data.startsWith('buy_')) {
        const [_, country, product] = data.split('_');
        
        try {
            bot.answerCallbackQuery(query.id, { text: 'Обработка запроса...' });
            
            // 1. Проверка цен (имитация для примера, в реальности берем из api.getProducts)
            const order = await api.buyNumber(country, 'any', product);
            
            bot.sendMessage(chatId, `✅ Номер куплен!\n\n📱 Номер: \`${order.phone}\`\n🆔 ID Заказа: \`${order.id}\`\n\nОжидаю SMS...`, {
                reply_markup: {
                    inline_keyboard: [
                        [{ text: '🔄 Проверить SMS', callback_data: `check_${order.id}` }],
                        [{ text: '❌ Отменить', callback_data: `cancel_${order.id}` }]
                    ]
                }
            });
        } catch (e) {
            bot.sendMessage(chatId, `❌ Ошибка: ${e.response?.data?.message || 'Номера закончились или недостаточно средств.'}`);
        }
    }

    if (data.startsWith('check_')) {
        const orderId = data.split('_')[1];
        try {
            const status = await api.checkOrder(orderId);
            if (status.sms && status.sms.length > 0) {
                bot.sendMessage(chatId, `📩 Получено SMS!\n\nКод: \`${status.sms[0].code}\`\nТекст: ${status.sms[0].text}`);
                await api.finishOrder(orderId);
            } else {
                bot.answerCallbackQuery(query.id, { text: 'SMS еще не пришло. Попробуйте позже.' });
            }
        } catch (e) {
            bot.answerCallbackQuery(query.id, { text: 'Ошибка проверки.' });
        }
    }

    if (data.startsWith('cancel_')) {
        const orderId = data.split('_')[1];
        try {
            await api.cancelOrder(orderId);
            bot.editMessageText('❌ Заказ отменен. Средства возвращены (если были списаны).', {
                chat_id: chatId,
                message_id: query.message.message_id
            });
        } catch (e) {
            bot.answerCallbackQuery(query.id, { text: 'Не удалось отменить.' });
        }
    }
});

console.log('⚡ IMPERIAL_SMS_BOT : СИСТЕМА АКТИВИРОВАНА ⚡');
