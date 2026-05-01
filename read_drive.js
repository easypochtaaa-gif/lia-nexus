const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function scanDrive() {
    console.log("[RECON] Connecting to active Chrome session...");
    
    try {
        const browser = await puppeteer.connect({
            browserURL: 'http://127.0.0.1:9222',
            defaultViewport: null
        });

        console.log("[RECON] Opening Google Drive...");
        const page = await browser.newPage();
        
        // Переходим в Диск
        await page.goto('https://drive.google.com/drive/my-drive', { waitUntil: 'networkidle2', timeout: 30000 });
        
        console.log("[RECON] Waiting for files to load...");
        // Ждем появления элементов с названиями файлов/папок
        await page.waitForSelector('c-wiz[role="main"]', { timeout: 15000 }).catch(() => console.log("Timeout waiting for main container"));
        await new Promise(r => setTimeout(r, 5000)); // Дополнительное ожидание рендера

        // Извлекаем текст из элементов, которые похожи на названия файлов (обычно они имеют класс, содержащий название, или атрибут aria-label)
        const items = await page.evaluate(() => {
            const fileElements = document.querySelectorAll('div[role="row"] div[aria-label], div[role="gridcell"] div[aria-label], c-wiz div[aria-label], c-wiz span[dir="ltr"]');
            let found = new Set();
            fileElements.forEach(el => {
                const label = el.getAttribute('aria-label') || el.innerText;
                if (label && label.length > 2 && label.length < 100 && !label.includes('Нажмите') && !label.includes('Выделить')) {
                    found.add(label.trim());
                }
            });
            return Array.from(found);
        });

        console.log(`\n[SUCCESS] Found ${items.length} items on the screen:\n`);
        items.forEach((item, index) => {
            console.log(`[${index + 1}] ${item}`);
        });

        if (items.length === 0) {
            console.log("[WARNING] Could not extract file names. You might not be logged in to cntrlstab@gmail.com, or the page structure is different.");
        }

        await page.close();
        console.log("\n[MISSION COMPLETE] Drive scan finished.");
        
    } catch (err) {
        console.error(`[ERROR] ${err.message}`);
    }
}

scanDrive();
