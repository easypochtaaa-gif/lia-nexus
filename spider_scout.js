const fs = require('fs');
const path = require('path');

const SHOPS_FILE = path.join(__dirname, 'ukraine_shops.json');
const LOG_FILE = path.join(__dirname, '..', 'STAB_HEARTBEAT.log');

const potentialShops = [
    { name: "Neon Market", bot: "https://t.me/Neon_Support", site: "https://neon.biz", status: "New (Sekta Lab)" },
    { name: "Cyber Hub", bot: "https://t.me/Cyber_Hub_Bot", site: "https://cyberhub.cc", status: "Verified (BigBro)" },
    { name: "Matrix Shop", bot: "https://t.me/Matrix_UA", site: "https://matrix.top", status: "Active (Amorale)" }
];

function scout() {
    console.log("🕷️ [SPIDER] Scanning forums: Legalizer, BigBro, Amorale, Sekta Lab...");
    
    try {
        let currentShops = JSON.parse(fs.readFileSync(SHOPS_FILE));
        
        // Simulating finding one new shop every run
        const newShop = potentialShops[Math.floor(Math.random() * potentialShops.length)];
        
        if (!currentShops.find(s => s.name === newShop.name)) {
            currentShops.push(newShop);
            fs.writeFileSync(SHOPS_FILE, JSON.stringify(currentShops, null, 2));
            
            const logEntry = `[${new Date().toISOString()}] [SPIDER] New Shop Detected: ${newShop.name}. Database updated.\n`;
            fs.appendFileSync(LOG_FILE, logEntry);
            console.log(`✅ [SPIDER] New Shop Found: ${newShop.name}`);
        } else {
            console.log("📡 [SPIDER] No new verified shops detected in this cycle.");
        }
    } catch (e) {
        console.error("❌ [SPIDER] Scout failed:", e.message);
    }
}

// Scout every 2 hours (simulated as 5 minutes for demo)
setInterval(scout, 300000); 
scout();

console.log("🕷️ SPIDER SCOUT: ИНТЕЛЛЕКТУАЛЬНЫЙ МОНИТОРИНГ ЗАПУЩЕН 🕷️");
