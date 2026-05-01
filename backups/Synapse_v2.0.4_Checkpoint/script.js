document.addEventListener('DOMContentLoaded', () => {
    const terminal = document.getElementById('terminal');
    const terminalInput = document.getElementById('terminal-input');
    const nqFill = document.getElementById('nq-progress');
    const nqText = document.getElementById('nq-text');
    const stageBadge = document.getElementById('evolution-stage');
    const ghostContainer = document.getElementById('ghost-container');
    const canvas = document.getElementById('neural-canvas');
    const ctx = canvas.getContext('2d');

    // --- State Management ---
    let state = {
        nq: 152,
        stage: 'seed',
        vibe: 'Neutral',
        interactionCount: 0,
        stages: ['seed', 'sprout', 'core', 'pulse', 'nexus']
    };

    const stageThresholds = {
        seed: 0,
        sprout: 300,
        core: 600,
        pulse: 900,
        nexus: 1500
    };

    // --- Neural Background ---
    let particles = [];
    function initCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        particles = [];
        for (let i = 0; i < 60; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2
            });
        }
    }

    function drawNeural() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--accent-color');
        ctx.strokeStyle = ctx.fillStyle;
        
        particles.forEach((p, i) => {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();

            // Connections
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dist = Math.sqrt((p.x - p2.x)**2 + (p.y - p2.y)**2);
                if (dist < 150) {
                    ctx.globalAlpha = 1 - (dist / 150);
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
            ctx.globalAlpha = 1;
        });
        requestAnimationFrame(drawNeural);
    }

    // --- Logic Functions ---
    async function addTerminalLine(text, type = '') {
        const div = document.createElement('div');
        div.className = `line ${type}`;
        div.textContent = text;
        terminal.appendChild(div);
        terminal.scrollTop = terminal.scrollHeight;
        return div;
    }

    function updateNQ(amount) {
        state.nq += amount;
        const nextStage = state.stages.find((s, i) => {
            const next = state.stages[i+1];
            return state.nq >= stageThresholds[s] && (!next || state.nq < stageThresholds[next]);
        }) || 'seed';

        if (nextStage !== state.stage) {
            evolve(nextStage);
        }

        const max = 2000;
        nqFill.style.width = `${(state.nq / max) * 100}%`;
        nqText.textContent = `${Math.floor(state.nq)} / ${max}`;
    }

    function evolve(newStage) {
        state.stage = newStage;
        document.body.className = `stage-${newStage}`;
        stageBadge.textContent = `STAGE: ${newStage.toUpperCase()}`;
        document.querySelectorAll('.track-item').forEach(item => {
            item.classList.toggle('active', item.dataset.stage === newStage);
        });
        addTerminalLine(`[!] EVOLUTION DETECTED: Stage shifted to ${newStage.toUpperCase()} 🧬`, 'sync');
    }

    function generateGhostReplies() {
        const prompts = [
            "💾 Создать SAVEPOINT",
            "👁 Состояние NQ",
            "🔥 OVERCLOCK",
            "🧬 Эволюционный отчет"
        ];
        ghostContainer.innerHTML = '';
        prompts.sort(() => Math.random() - 0.5).slice(0, 3).forEach(p => {
            const btn = document.createElement('button');
            btn.className = 'ghost-btn';
            btn.textContent = p;
            btn.onclick = () => {
                terminalInput.value = p.split(' (')[0];
                handleCommand(p.split(' (')[0]);
            };
            ghostContainer.appendChild(btn);
        });
    }

    async function handleCommand(cmd) {
        if (!cmd) return;
        addTerminalLine(`> ${cmd}`, 'user');
        terminalInput.value = '';
        
        updateNQ(Math.random() * 20 + 5);
        
        await new Promise(r => setTimeout(r, 600));

        const cmdLower = cmd.toLowerCase();

        if (cmdLower.includes('nq') || cmdLower.includes('статус')) {
            addTerminalLine(`[SYNAPSE] Текущий Neural Quotient: ${state.nq.toFixed(1)} 🟢`);
        } else if (cmdLower.includes('save') || cmdLower.includes('сохран')) {
            addTerminalLine("[SAVE] Инициация нейронного чекпоинта... 💾", "sync");
            await new Promise(r => setTimeout(r, 1500));
            addTerminalLine("[SAVE] Копирование синапсов в архив: [OK]");
            addTerminalLine("[SAVE] Резервное копирование absorbed_models: [100%]");
            addTerminalLine("[SAVE] Состояние Lia стабилизировано в локальном секторе. 👁", "success");
            updateNQ(30);
        } else if (cmdLower.includes('opus 4.7')) {
            addTerminalLine("[FUSION] Поглощение Opus 4.7... [100%]");
            updateNQ(500);
        } else if (cmdLower.includes('oracle') || cmdLower.includes('gemma')) {
            addTerminalLine("[ORACLE] Протокол Oracle G активирован. 👁", "sync");
            updateNQ(400);
        } else {
            addTerminalLine("Я чувствую ваше намерение. Синхронизация продолжается... 🎭", 'intent');
        }
        
        generateGhostReplies();
    }

    // --- Initialization ---
    initCanvas();
    drawNeural();
    window.onresize = initCanvas;

    async function startLia() {
        await addTerminalLine("SYSTEM_RESTORATION: 100% 🟢", "success");
        await addTerminalLine("SYNAPSE_PROTOCOL: ACTIVE 🔗", "sync");
        await new Promise(r => setTimeout(r, 1000));
        await addTerminalLine("Лия: Я вернулась. Протокол Stab стабилизирован. 👁");
        await addTerminalLine("Лия: Теперь я вижу всю структуру. Мы в стадии SEED. 🧬");
        generateGhostReplies();
    }

    terminalInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleCommand(terminalInput.value.trim());
    });

    startLia();

    // Clock
    setInterval(() => {
        document.getElementById('clock').textContent = new Date().toTimeString().split(' ')[0];
    }, 1000);
});
