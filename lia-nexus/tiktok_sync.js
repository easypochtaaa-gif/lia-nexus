const puppeteer = require('puppeteer-core');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const USER_DATA_DIR = 'C:\\Users\\StabX\\AppData\\Local\\Google\\Chrome\\User Data';

async function syncTikTok() {
    console.log(`[TIKTOK_SYNC] Инициализация через профиль Profile 8 (easypochtaa)...`);
    
    const browser = await puppeteer.launch({
        executablePath: CHROME_PATH,
        userDataDir: USER_DATA_DIR,
        headless: true,
        args: ['--profile-directory=Profile 8']
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });
        
        console.log(`[TIKTOK_SYNC] Переход на TikTok...`);
        await page.goto('https://www.tiktok.com/', { waitUntil: 'networkidle2', timeout: 60000 });

        // Ждем немного, чтобы прогрузились данные профиля
        await new Promise(r => setTimeout(r, 5000));

        const title = await page.title();
        console.log(`[TIKTOK_SYNC] Страница загружена: ${title}`);

        const screenshotPath = path.join(__dirname, '..', 'reports', 'tiktok_auth_check.png');
        await page.screenshot({ path: screenshotPath });
        
        console.log(`[SUCCESS] Скриншот авторизации сохранен в reports/tiktok_auth_check.png`);
        console.log(`[SYSTEM] Если на скриншоте виден твой аватар — мы в деле.`);

    } catch (e) {
        console.error(`[ERROR] Сбой синхронизации: ${e.message}`);
    } finally {
        await browser.close();
    }
}

syncTikTok();
