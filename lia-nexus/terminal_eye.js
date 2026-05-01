const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const URL = process.argv[2] || 'https://google.com';
const REPORT_PATH = path.join(__dirname, '..', 'reports', 'terminal_browser_result.md');

async function run() {
    console.log(`[TERMINAL_EYE] Инициализация...`);
    console.log(`[TERMINAL_EYE] Цель: ${URL}`);

    const browser = await puppeteer.launch({
        executablePath: CHROME_PATH,
        headless: true // Установи в false, если хочешь видеть, как открывается окно
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });
        
        console.log(`[TERMINAL_EYE] Переход по ссылке...`);
        await page.goto(URL, { waitUntil: 'networkidle2', timeout: 30000 });

        const title = await page.title();
        const text = await page.evaluate(() => document.body.innerText);
        const screenshotPath = path.join(__dirname, '..', 'reports', 'last_scan.png');
        
        await page.screenshot({ path: screenshotPath });

        const report = `# BROWSER SCAN REPORT\n\n**URL:** ${URL}\n**TITLE:** ${title}\n**TIMESTAMP:** ${new Date().toISOString()}\n\n## CONTENT PREVIEW:\n${text.substring(0, 1000)}...\n\n[SCREENSHOT SAVED AS last_scan.png]`;
        
        fs.writeFileSync(REPORT_PATH, report);
        console.log(`[SUCCESS] Скан завершен. Отчет: reports/terminal_browser_result.md`);

    } catch (e) {
        console.error(`[ERROR] Сбой сканирования: ${e.message}`);
        fs.writeFileSync(REPORT_PATH, `# BROWSER ERROR\n\n${e.message}`);
    } finally {
        await browser.close();
    }
}

run();
