const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function readNotebook() {
    console.log("[RECON] Connecting to active browser session...");
    
    try {
        const browser = await puppeteer.connect({
            browserURL: 'http://127.0.0.1:9222',
            defaultViewport: null
        });

        const pages = await browser.pages();
        console.log(`[RECON] Found ${pages.length} open tabs.`);

        // Find NotebookLM tabs
        for (const page of pages) {
            const url = page.url();
            const title = await page.title();
            
            if (url.includes('notebooklm.google.com/notebook/22c025d7')) {
                console.log(`[TARGET FOUND] ${title}`);
                console.log(`[URL] ${url}`);
                
                // Extract all visible text
                const textContent = await page.evaluate(() => {
                    return document.body.innerText;
                });
                
                // Extract full HTML for deeper analysis
                const htmlContent = await page.evaluate(() => {
                    return document.body.innerHTML;
                });
                
                // Save to files
                fs.writeFileSync('notebook_text.txt', textContent, 'utf8');
                fs.writeFileSync('notebook_html.txt', htmlContent, 'utf8');
                
                console.log(`[SUCCESS] Extracted ${textContent.length} characters of text.`);
                console.log("--- TEXT CONTENT ---");
                console.log(textContent.substring(0, 3000));
                console.log("--- END PREVIEW ---");
            }
        }

        // Now try the specific artifact URLs
        const artifactUrls = [
            'https://notebooklm.google.com/notebook/22c025d7-ec82-4dfa-ae31-dadd4adcb054/artifact/095c100f-576c-40ca-bbcf-bf6197ec2f9e',
            'https://notebooklm.google.com/notebook/22c025d7-ec82-4dfa-ae31-dadd4adcb054/artifact/d8994c06-dc0d-45be-b6ec-367362f511a0'
        ];

        for (let i = 0; i < artifactUrls.length; i++) {
            console.log(`\n[RECON] Opening artifact ${i + 1}...`);
            const page = await browser.newPage();
            await page.goto(artifactUrls[i], { waitUntil: 'networkidle2', timeout: 15000 });
            await new Promise(r => setTimeout(r, 3000));
            
            const text = await page.evaluate(() => document.body.innerText);
            const filename = `artifact_${i + 1}.txt`;
            fs.writeFileSync(filename, text, 'utf8');
            console.log(`[SUCCESS] Artifact ${i + 1}: ${text.length} chars saved to ${filename}`);
            console.log(text.substring(0, 2000));
            await page.close();
        }

        console.log("\n[MISSION COMPLETE] All intel extracted.");
        
    } catch (err) {
        console.error(`[ERROR] ${err.message}`);
        console.log("[TIP] Make sure Chrome is running with --remote-debugging-port=9222");
    }
}

readNotebook();
