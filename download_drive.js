const puppeteer = require('puppeteer-core');

async function downloadFolder() {
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
        await page.waitForSelector('c-wiz[role="main"]', { timeout: 15000 }).catch(() => console.log("Timeout waiting for main container"));
        await new Promise(r => setTimeout(r, 5000));

        // Находим папку "санапс стабус" и кликаем по ней правой кнопкой мыши
        const folderClicked = await page.evaluate(() => {
            const elements = Array.from(document.querySelectorAll('div[role="row"], div[role="gridcell"]'));
            for (let el of elements) {
                const label = el.getAttribute('aria-label') || '';
                const text = el.innerText || '';
                if (text.includes('санапс стабус') || label.includes('санапс стабус')) {
                    // Имитируем правый клик
                    const event = new MouseEvent('contextmenu', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: el.getBoundingClientRect().x + 10,
                        clientY: el.getBoundingClientRect().y + 10
                    });
                    el.dispatchEvent(event);
                    return true;
                }
            }
            return false;
        });

        if (folderClicked) {
            console.log("[SUCCESS] Right-clicked on 'санапс стабус'. Waiting for context menu...");
            await new Promise(r => setTimeout(r, 2000));

            // Ищем пункт меню "Скачать" (Download)
            const downloadClicked = await page.evaluate(() => {
                const menuItems = Array.from(document.querySelectorAll('div[role="menuitem"]'));
                for (let item of menuItems) {
                    if (item.innerText.includes('Скачать') || item.innerText.includes('Download')) {
                        item.click();
                        return true;
                    }
                }
                return false;
            });

            if (downloadClicked) {
                console.log("[SUCCESS] Clicked 'Скачать' (Download). Zipping and downloading started...");
                console.log("[INFO] The file will be saved to your default Downloads folder.");
            } else {
                console.log("[ERROR] Could not find 'Скачать' in the context menu.");
            }
        } else {
            console.log("[ERROR] Could not find folder 'санапс стабус'.");
        }

        // Ждем немного перед закрытием, чтобы дать команде скачивания пройти
        await new Promise(r => setTimeout(r, 5000));
        await page.close();
        browser.disconnect();
    } catch (err) {
        console.error(`[ERROR] ${err.message}`);
    }
}

downloadFolder();
