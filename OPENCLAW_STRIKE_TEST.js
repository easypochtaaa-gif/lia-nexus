const openclaw = require('./openclaw_stealth');

(async () => {
    console.log("🌀 [NEURAL_BRIDGE] Инициация тестового удара OpenClaw...");
    try {
        const target = 'https://netpeak.net/ru/'; // Реальная цель для теста разведки
        console.log(`🎯 [TARGET] ${target}`);
        
        const data = await openclaw.extractB2B(target, 'IMPERIAL_RECON');
        
        console.log("\n💎 [EXTRACTION_REPORT] 💎");
        console.log(`Title: ${data.title}`);
        console.log(`Emails found: ${data.emails.join(', ') || 'None found'}`);
        console.log(`Phones found: ${data.phones.length} items extracted.`);
        
        if (data.emails.length > 0) {
            console.log("\n✅ [STATUS] ТЕСТ УСПЕШЕН. Система способна извлекать реальные данные.");
        } else {
            console.log("\n⚠️ [STATUS] Данные не найдены, но структура сайта проанализирована.");
        }
        
    } catch (e) {
        console.error(`\n❌ [ERROR] Сбой модуля Stealth: ${e.message}`);
    }
})();
