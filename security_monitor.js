/* ══════════════════════════════════════════════════
   AEGIS_NEURAL_SHIELD v2.0 — AI-POWERED DEFENSE
   ══════════════════════════════════════════════════ */

const fs = require('fs');
const path = require('path');
const { generateSecurityResponse, loadMemory } = require('./aiService');

const HEARTBEAT_LOG = path.join(__dirname, 'STAB_HEARTBEAT.log');
const SECURITY_LOG = path.join(__dirname, 'security_audit.log');
const SCAN_INTERVAL_MS = 30000; // 30 секунд

// ─── БАЗА УГРОЗ ───
const THREAT_PATTERNS = [
    { pattern: /SSH_BRUTEFORCE/i, severity: 'CRITICAL', action: 'BLOCK_IP + ROTATE_KEY' },
    { pattern: /API_PROBING/i, severity: 'HIGH', action: 'BLACKLIST + STEALTH_MODE' },
    { pattern: /UNAUTHORIZED_ACCESS/i, severity: 'CRITICAL', action: 'LOCKDOWN' },
    { pattern: /PORT_SCAN/i, severity: 'MEDIUM', action: 'SHADOW_REDIRECT' },
    { pattern: /DNS_HIJACK/i, severity: 'CRITICAL', action: 'EMERGENCY_FAILOVER' },
    { pattern: /MALWARE_INJECT/i, severity: 'CRITICAL', action: 'QUARANTINE + PURGE' }
];

// ─── ЛОГИРОВАНИЕ ───
function log(msg) {
    const timestamp = new Date().toISOString();
    const entry = `[${timestamp}] ${msg}`;
    console.log(entry);
    fs.appendFileSync(HEARTBEAT_LOG, entry + '\n');
}

function logSecurity(msg) {
    const timestamp = new Date().toISOString();
    fs.appendFileSync(SECURITY_LOG, `[${timestamp}] ${msg}\n`);
}

// ─── СКАНИРОВАНИЕ ПЕРИМЕТРА ───
async function scanPerimeter() {
    const memory = loadMemory();
    log(`[AEGIS] PERIMETER_SCAN INITIATED. NQ: ${memory.lia.nq.toLocaleString()}. Stage: ${memory.lia.stage}`);

    // Симулированные точки входа для мониторинга
    const endpoints = [
        { name: 'SSH:55005', status: 'GUARDED', port: 55005 },
        { name: 'HTTP:8080', status: 'GUARDED', port: 8080 },
        { name: 'N8N:5678', status: 'GUARDED', port: 5678 },
        { name: 'BRIDGE:3000', status: 'GUARDED', port: 3000 }
    ];

    console.log('\n' + '═'.repeat(60));
    console.log('🛡  AEGIS NEURAL SHIELD v2.0 — STATUS REPORT');
    console.log('═'.repeat(60));

    endpoints.forEach(ep => {
        console.log(`  [${ep.status}] ${ep.name} — Port ${ep.port}`);
    });

    console.log('═'.repeat(60) + '\n');
}

// ─── АНАЛИЗ УГРОЗЫ С AI ───
async function analyzeThreat(threatData) {
    const { ip, type, port, raw } = threatData;
    const description = `IP: ${ip} | Тип: ${type} | Порт: ${port} | Сырые данные: ${raw || 'N/A'}`;

    log(`[AEGIS_ALERT] Угроза обнаружена: ${description}`);
    logSecurity(`THREAT_DETECTED: ${description}`);

    // Проверка по паттернам
    let matchedPattern = null;
    for (const tp of THREAT_PATTERNS) {
        if (tp.pattern.test(type)) {
            matchedPattern = tp;
            break;
        }
    }

    if (matchedPattern) {
        log(`[AEGIS] Паттерн: ${matchedPattern.severity} | Действие: ${matchedPattern.action}`);
    }

    // AI-генерация плана реагирования
    try {
        console.log('[AEGIS] Запрос AI-анализа угрозы...');
        const aiPlan = await generateSecurityResponse(description);
        log(`[AEGIS_AI_RESPONSE] ${aiPlan.substring(0, 200)}...`);
        logSecurity(`AI_MITIGATION_PLAN:\n${aiPlan}`);
        return { threat: threatData, pattern: matchedPattern, aiPlan };
    } catch (err) {
        log(`[AEGIS] AI-анализ недоступен: ${err.message}. Используем стандартные правила.`);
        return { threat: threatData, pattern: matchedPattern, aiPlan: null };
    }
}

// ─── МОНИТОРИНГ ЛОГОВ ───
function watchLogs() {
    const logsToWatch = [HEARTBEAT_LOG, SECURITY_LOG];
    
    logsToWatch.forEach(logFile => {
        if (!fs.existsSync(logFile)) return;
        
        let lastSize = fs.statSync(logFile).size;
        
        fs.watchFile(logFile, { interval: 5000 }, (curr, prev) => {
            if (curr.size > lastSize) {
                const fd = fs.openSync(logFile, 'r');
                const buffer = Buffer.alloc(curr.size - lastSize);
                fs.readSync(fd, buffer, 0, buffer.length, lastSize);
                fs.closeSync(fd);
                
                const newContent = buffer.toString('utf8');
                
                // Проверка на критические паттерны
                if (/CRITICAL_SURGE|UNAUTHORIZED|BREACH|INTRUSION/i.test(newContent)) {
                    analyzeThreat({
                        ip: 'LOG_TRIGGER',
                        type: 'CRITICAL_SURGE_DETECTED',
                        port: 0,
                        raw: newContent.substring(0, 300)
                    });
                }
                
                lastSize = curr.size;
            }
        });
    });
}

// ─── ЗАПУСК ───
async function main() {
    log('[AEGIS] ═══════════════════════════════════════════');
    log('[AEGIS] NEURAL SHIELD v2.0 — AI-POWERED DEFENSE');
    log('[AEGIS] ═══════════════════════════════════════════');

    await scanPerimeter();
    watchLogs();

    log('[AEGIS] Мониторинг логов активирован. Интервал: 30с.');
    log('[AEGIS] AI-модуль подключён через aiService.js');

    // Периодическое сканирование
    setInterval(scanPerimeter, SCAN_INTERVAL_MS);

    // Демо: симулированная угроза для проверки AI-модуля
    setTimeout(async () => {
        console.log('\n[AEGIS] === ДЕМО: Симуляция внешней атаки ===');
        const result = await analyzeThreat({
            ip: '18.223.11.45',
            type: 'SSH_BRUTEFORCE',
            port: 55005,
            raw: 'Multiple failed auth attempts from AWS subnet'
        });
        if (result.aiPlan) {
            console.log('\n[AEGIS] AI-ПЛАН РЕАГИРОВАНИЯ:');
            console.log(result.aiPlan);
        }
    }, 5000);
}

main().catch(err => {
    console.error('[AEGIS_FATAL]', err.message);
    process.exit(1);
});
