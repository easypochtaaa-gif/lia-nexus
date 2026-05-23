
const { spawn } = require('child_process');
const path = require('path');

/**
 * 🌀 LIA_ORCHESTRATOR v1.0
 * Запуск всех систем Империи одной командой.
 */

function startProcess(name, scriptPath, interpreter = 'node') {
    console.log(`[ORCHESTRATOR] Запуск узла: ${name}...`);
    const child = spawn(interpreter, [scriptPath], { stdio: 'inherit', shell: true });

    child.on('exit', (code) => {
        console.log(`[ORCHESTRATOR] Узел ${name} завершил работу (код ${code}). Перезапуск через 5 секунд...`);
        setTimeout(() => startProcess(name, scriptPath, interpreter), 5000);
    });
}

// Запуск всех систем
startProcess('STAB_LIA (SMS)', path.join(__dirname, 'sms_bot.js'));
startProcess('MASTER_LIA (TG)', path.join(__dirname, 'telegram_bot.js'));
startProcess('OMEGA_HUB (SERVER)', path.join(__dirname, 'server.js'));
startProcess('SWARM_CORE (PYTHON)', path.join(__dirname, 'autonomous_swarm', 'agent_swarm.py'), 'python');

console.log('⚡ ВСЕ СИСТЕМЫ СИНХРОНИЗИРОВАНЫ. ИМПЕРИЯ В СЕТИ. ⚡');
