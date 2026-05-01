const puppeteer = require('puppeteer-core');
const axios = require('axios');

async function connectToChrome() {
    console.log(`[REMOTE_BIND] Попытка подключения к 127.0.0.1:9222...`);
    
    try {
        // Получаем WebSocket URL от запущенного браузера
        const response = await axios.get('http://127.0.0.1:9222/json/version');
        const webSocketDebuggerUrl = response.data.webSocketDebuggerUrl;
        
        console.log(`[REMOTE_BIND] WS URL получен. Подключаюсь...`);
        
        const browser = await puppeteer.connect({
            browserWSEndpoint: webSocketDebuggerUrl,
            defaultViewport: null
        });

        const pages = await browser.pages();
        console.log(`[REMOTE_BIND] Найдено вкладок: ${pages.length}`);

        let tiktokFound = false;
        for (const page of pages) {
            const url = await page.url();
            console.log(`[TAB] ${url}`);
            
            if (url.includes('tiktok.com')) {
                tiktokFound = true;
                console.log(`[SUCCESS] TikTok обнаружен в активной вкладке!`);
                const title = await page.title();
                console.log(`[DATA] Заголовок: ${title}`);
                
                // Пробуем считать никнейм
                const nickname = await page.evaluate(() => {
                    const el = document.querySelector('[data-e2e="user-title"]');
                    return el ? el.innerText : 'Никнейм не найден в DOM';
                });
                console.log(`[RESULT] Твой никнейм: ${nickname}`);
            }
        }

        if (!tiktokFound) {
            console.log(`[WARNING] TikTok не найден среди открытых вкладок. Открой его, и я увижу.`);
        }

        await browser.disconnect();

    } catch (e) {
        console.error(`[ERROR] Не удалось подключиться: ${e.message}`);
        console.log(`[HELP] Убедись, что Chrome запущен с флагом --remote-debugging-port=9222`);
    }
}

connectToChrome();
