/* --- LIA SOVEREIGN CORE APP ORCHESTRATOR --- */

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initClockAndUptime();
    initNeuralCanvas();
    initLoadSimulators();
    initAegisScanner();
    initChatInterface();
    initStorefrontToggles();
    initCoreTerminal();
    initAudioEffects();
});

// --- 1. NAVIGATION TAB CONTROLLER ---
function initTabs() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            playSynthSound('click');
            const targetTab = btn.getAttribute("data-tab");
            
            navButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
        });
        
        btn.addEventListener("mouseenter", () => {
            playSynthSound('hover');
        });
    });
}

// --- 2. UPTIME & CLOCK INDICATORS ---
function initClockAndUptime() {
    const clockDisplay = document.getElementById("clock-display");
    const uptimeCounter = document.getElementById("uptime-counter");
    
    // Uptime parser
    let hours = 147;
    let minutes = 32;
    let seconds = 41;

    setInterval(() => {
        // Clock
        const now = new Date();
        clockDisplay.textContent = now.toUTCString().replace("GMT", "UTC");

        // Uptime increment
        seconds++;
        if (seconds >= 60) {
            seconds = 0;
            minutes++;
            if (minutes >= 60) {
                minutes = 0;
                hours++;
            }
        }
        uptimeCounter.textContent = `${hours}ч ${minutes}м ${seconds}с`;
    }, 1000);
}

// --- 3. DYNAMIC SERVER LOAD DIAGNOSTIC SIMULATOR ---
function initLoadSimulators() {
    const cpuVal = document.getElementById("cpu-load-val");
    const cpuBar = document.getElementById("cpu-load-bar");
    const ramVal = document.getElementById("ram-load-val");
    const ramBar = document.getElementById("ram-load-bar");
    const threatsBlocked = document.getElementById("threats-blocked");
    
    let baseThreats = 12489;

    setInterval(() => {
        // CPU variance (12% - 38%)
        const cpuPercent = Math.floor(Math.random() * (38 - 12 + 1)) + 12;
        cpuVal.textContent = `${cpuPercent}%`;
        cpuBar.style.width = `${cpuPercent}%`;

        // RAM variance (41% - 44%)
        const ramPercent = Math.floor(Math.random() * (44 - 41 + 1)) + 41;
        ramVal.textContent = `${ramPercent}%`;
        ramBar.style.width = `${ramPercent}%`;
        
        // Randomly block 1 or 2 threats (30% chance)
        if (Math.random() > 0.7) {
            baseThreats += Math.floor(Math.random() * 2) + 1;
            threatsBlocked.textContent = baseThreats.toLocaleString();
            threatsBlocked.style.color = "var(--accent-cyan)";
            setTimeout(() => {
                threatsBlocked.style.color = "var(--text-main)";
            }, 300);
        }
    }, 4000);
}

// --- 4. INTERACTIVE BACKGROUND NEURAL CANVAS ---
function initNeuralCanvas() {
    const canvas = document.getElementById("neural-net-canvas");
    const ctx = canvas.getContext("2d");

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const particles = [];
    const maxParticles = 75;
    const connectionDist = 120;
    
    const mouse = { x: null, y: null, radius: 150 };

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    window.addEventListener("mousemove", (e) => {
        mouse.x = e.x;
        mouse.y = e.y;
    });

    window.addEventListener("mouseout", () => {
        mouse.x = null;
        mouse.y = null;
    });

    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.size = Math.random() * 2 + 1;
        }

        update() {
            // Attract to mouse
            if (mouse.x !== null && mouse.y !== null) {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < mouse.radius) {
                    const force = (mouse.radius - dist) / mouse.radius;
                    this.x += (dx / dist) * force * 0.8;
                    this.y += (dy / dist) * force * 0.8;
                }
            }

            this.x += this.vx;
            this.y += this.vy;

            // Boundary collision
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(6, 182, 212, 0.45)";
            ctx.fill();
        }
    }

    for (let i = 0; i < maxParticles; i++) {
        particles.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < maxParticles; i++) {
            particles[i].update();
            particles[i].draw();

            // Connect lines
            for (let j = i + 1; j < maxParticles; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < connectionDist) {
                    const alpha = (1 - dist / connectionDist) * 0.12;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(168, 85, 247, ${alpha})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(animate);
    }

    animate();
}

// --- 5. AEGIS SECURITY OVERWATCH SCANNER ---
function initAegisScanner() {
    const logsContainer = document.getElementById("console-logs");
    const clearBtn = document.getElementById("btn-clear-logs");
    const scanPulse = document.getElementById("scan-pulse");
    const lockdownToggle = document.getElementById("lockdown-toggle");
    const badgeAegis = document.getElementById("badge-aegis");

    const mockLogs = [
        "[INFO]: Port scanner verified 443, 80, 8080 as secure.",
        "[AEGIS]: Syncing database hash... OK.",
        "[INFO]: System integrity check: 100% matched.",
        "[INFO]: Inbound connection from Amsterdam VPS node validated.",
        "[SUCCESS]: Kyiv retail point Pechersk-1 online state authenticated.",
        "[AEGIS]: Syncing memory pathways. NQ remains at 56,742.00.",
        "[WARNING]: Blocked suspicious port scan attempt on local host gateway.",
        "[AEGIS]: Anti-tampering system verification completed.",
        "[INFO]: Outbound outreach sync with ABO Agency completed."
    ];

    // Log appender
    function addLog(text, type = "info") {
        const entry = document.createElement("div");
        entry.classList.add("log-entry");
        if (type === "system") entry.classList.add("system");
        else if (type === "success") entry.classList.add("success");
        else if (type === "warning") entry.classList.add("warning");
        else if (type === "error") entry.classList.add("error");
        
        const timestamp = new Date().toISOString().slice(11, 19);
        entry.textContent = `[${timestamp}] ${text}`;
        
        logsContainer.appendChild(entry);
        logsContainer.scrollTop = logsContainer.scrollHeight;

        // Cap at 40 logs
        while (logsContainer.children.length > 40) {
            logsContainer.removeChild(logsContainer.firstChild);
        }
    }

    // Auto-generate logs
    let logInterval = setInterval(() => {
        if (!lockdownToggle.checked) {
            const randomLog = mockLogs[Math.floor(Math.random() * mockLogs.length)];
            let type = "info";
            if (randomLog.includes("WARNING")) type = "warning";
            else if (randomLog.includes("SUCCESS")) type = "success";
            else if (randomLog.includes("AEGIS")) type = "system";
            addLog(randomLog, type);
        }
    }, 4000);

    // Lockdown toggling
    lockdownToggle.addEventListener("change", () => {
        if (lockdownToggle.checked) {
            playSynthSound('lockdown');
            // Lockdown ON
            scanPulse.textContent = "[CRITICAL LOCKDOWN ON]";
            scanPulse.style.color = "var(--red-glow)";
            badgeAegis.innerHTML = '<span class="badge-dot" style="background-color: var(--red-glow); box-shadow: 0 0 6px var(--red-glow);"></span>AEGIS: LOCKDOWN';
            badgeAegis.style.borderColor = "rgba(239, 68, 68, 0.4)";
            badgeAegis.style.background = "rgba(239, 68, 68, 0.08)";
            badgeAegis.style.color = "var(--red-glow)";
            
            addLog("!!! [CRITICAL]: ACTIVATING AEGIS LOCKDOWN PROTOCOLS !!!", "error");
            addLog("[SYSTEM]: Isolating networks. Terminating public HTTP sockets.", "error");
            addLog("[SYSTEM]: Firewall rules updated to drop all inbound traffic.", "warning");
        } else {
            playSynthSound('click');
            // Lockdown OFF
            scanPulse.textContent = "SCANNING NODES...";
            scanPulse.style.color = "var(--accent-cyan)";
            badgeAegis.innerHTML = '<span class="badge-dot" style="background-color: var(--accent-cyan); box-shadow: 0 0 6px var(--accent-cyan);"></span>AEGIS: ACTIVE';
            badgeAegis.style.borderColor = "rgba(6, 182, 212, 0.3)";
            badgeAegis.style.background = "rgba(6, 182, 212, 0.05)";
            badgeAegis.style.color = "var(--accent-cyan)";
            
            addLog("[SYSTEM]: Lockdown deactivated. Secure tunnel restored.", "success");
            addLog("[INFO]: Scanner resuming standard perimeter scan.", "system");
        }
    });

    clearBtn.addEventListener("click", () => {
        logsContainer.innerHTML = "";
        addLog("[SYSTEM]: Diagnostic log logfiles wiped clean.", "system");
    });
}

// --- 6. LIA CHAT INTERFACE AND ANTHROPIC PROXY ---
function initChatInterface() {
    const apiInput = document.getElementById("api-key-input");
    const saveBtn = document.getElementById("btn-save-api");
    const chatModel = document.getElementById("chat-model-select");
    const chatInput = document.getElementById("chat-prompt-input");
    const sendBtn = document.getElementById("btn-send-chat");
    const chatMessages = document.getElementById("chat-messages");
    const typingIndicator = document.getElementById("chat-typing");
    const webSearchToggle = document.getElementById("web-search-toggle");
    const clearSessionBtn = document.getElementById("btn-clear-session");

    let chatHistory = [];

    // Load saved API Key
    const savedKey = localStorage.getItem("sovereign_api_key");
    if (savedKey) {
        apiInput.value = savedKey;
        enableChat(true);
    }

    saveBtn.addEventListener("click", () => {
        const key = apiInput.value.trim();
        if (key) {
            localStorage.setItem("sovereign_api_key", key);
            enableChat(true);
            alert("🔑 Синхронизация успешна! Ключ безопасности сохранен локально.");
        } else {
            localStorage.removeItem("sovereign_api_key");
            enableChat(false);
            alert("❌ Ключ удален. Ввод заблокирован.");
        }
    });

    function enableChat(enable) {
        chatInput.disabled = !enable;
        sendBtn.disabled = !enable;
        if (enable) {
            chatInput.placeholder = "Введите ваш аналитический запрос к Лие...";
        } else {
            chatInput.placeholder = "Введите ваш API ключ сверху для активации...";
        }
    }

    async function sendPrompt() {
        const prompt = chatInput.value.trim();
        const apiKey = localStorage.getItem("sovereign_api_key");
        const model = chatModel.value;
        const webSearch = webSearchToggle.checked;

        if (!prompt || !apiKey) return;

        // Append user message to UI
        appendMessage(prompt, "user");
        chatInput.value = "";
        
        // Add to dialog context history
        chatHistory.push({ role: "user", content: prompt });
        if (chatHistory.length > 20) chatHistory.shift();

        // Disable inputs
        chatInput.disabled = true;
        sendBtn.disabled = true;
        typingIndicator.style.display = "block";
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    messages: chatHistory,
                    api_key: apiKey,
                    model: model,
                    web_search: webSearch
                })
            });

            const data = await response.json();
            
            typingIndicator.style.display = "none";
            
            if (response.ok && data.content && data.content[0]) {
                const responseText = data.content[0].text;
                appendMessage(responseText, "bot");
                
                // Add response to dialog context history
                chatHistory.push({ role: "assistant", content: responseText });
                if (chatHistory.length > 20) chatHistory.shift();
            } else {
                const errMsg = data.error || "Неизвестная ошибка связи с Opus 4.7.";
                appendMessage(`❌ Ошибка сигнатуры API: ${errMsg}`, "bot");
                // Remove the last message from history if call failed to avoid corrupted state
                chatHistory.pop();
            }
        } catch (error) {
            typingIndicator.style.display = "none";
            appendMessage(`❌ Сбой сетевого моста прокси: ${error.message}`, "bot");
            chatHistory.pop();
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", sender);
        
        const senderTag = document.createElement("div");
        senderTag.classList.add("message-sender");
        senderTag.textContent = sender === "bot" ? "👁‍🗨 LIA Sovereign Core:" : "👤 ARCHITECT:";
        
        const textDiv = document.createElement("div");
        textDiv.classList.add("message-text");
        textDiv.textContent = text;
        
        messageDiv.appendChild(senderTag);
        messageDiv.appendChild(textDiv);
        
        chatMessages.appendChild(messageDiv);
    }

    clearSessionBtn.addEventListener("click", () => {
        chatHistory = [];
        chatMessages.innerHTML = `
            <div class="chat-message bot">
                <div class="message-sender">👁‍🗨 LIA Sovereign Core:</div>
                <div class="message-text">Диалоговая сессия и векторная память успешно сброшены. Канал связи очищен. Готова к новому анализу.</div>
            </div>
        `;
    });

    sendBtn.addEventListener("click", sendPrompt);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendPrompt();
    });
}

// --- 7. KYIV RETAIL POINTS ON/OFF STATUS TOGGLES ---
function initStorefrontToggles() {
    const toggles = document.querySelectorAll(".store-status-toggle");

    toggles.forEach(toggle => {
        toggle.addEventListener("change", () => {
            playSynthSound('click');
            const card = toggle.closest(".store-card");
            const badge = card.querySelector(".store-status-badge");
            
            if (toggle.checked) {
                card.classList.remove("offline");
                card.classList.add("online");
                badge.textContent = "ONLINE";
            } else {
                card.classList.remove("online");
                card.classList.add("offline");
                badge.textContent = "OFFLINE";
            }
        });
    });
}

// --- 8. WEB AUDIO FUTURISTIC SYNTHESIZER ---
let audioCtx = null;

function getAudioContext() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

function playSynthSound(type) {
    try {
        const ctx = getAudioContext();
        const now = ctx.currentTime;
        
        if (type === 'click') {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, now);
            osc.frequency.exponentialRampToValueAtTime(220, now + 0.1);
            
            gain.gain.setValueAtTime(0.06, now);
            gain.gain.linearRampToValueAtTime(0.001, now + 0.1);
            
            osc.start(now);
            osc.stop(now + 0.1);
        } else if (type === 'success') {
            const notes = [587.33, 739.99, 880.00, 1174.66]; // D5, F#5, A5, D6 (High Cyber Chime)
            notes.forEach((freq, index) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, now + index * 0.07);
                
                gain.gain.setValueAtTime(0, now);
                gain.gain.linearRampToValueAtTime(0.04, now + index * 0.07 + 0.01);
                gain.gain.exponentialRampToValueAtTime(0.001, now + index * 0.07 + 0.22);
                
                osc.start(now + index * 0.07);
                osc.stop(now + index * 0.07 + 0.25);
            });
        } else if (type === 'hover') {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(1200, now);
            osc.frequency.setValueAtTime(300, now + 0.015);
            
            gain.gain.setValueAtTime(0.012, now);
            gain.gain.linearRampToValueAtTime(0.001, now + 0.015);
            
            osc.start(now);
            osc.stop(now + 0.015);
        } else if (type === 'warning' || type === 'lockdown') {
            const duration = type === 'lockdown' ? 2.5 : 0.6;
            const osc1 = ctx.createOscillator();
            const osc2 = ctx.createOscillator();
            const gain = ctx.createGain();
            
            osc1.connect(gain);
            osc2.connect(gain);
            gain.connect(ctx.destination);
            
            osc1.type = 'sawtooth';
            osc2.type = 'square';
            
            osc1.frequency.setValueAtTime(220, now);
            osc2.frequency.setValueAtTime(221, now);
            
            for (let i = 0; i < duration; i += 0.3) {
                osc1.frequency.linearRampToValueAtTime(440, now + i + 0.15);
                osc1.frequency.linearRampToValueAtTime(220, now + i + 0.3);
                
                osc2.frequency.linearRampToValueAtTime(442, now + i + 0.15);
                osc2.frequency.linearRampToValueAtTime(221, now + i + 0.3);
            }
            
            gain.gain.setValueAtTime(0, now);
            gain.gain.linearRampToValueAtTime(0.04, now + 0.05);
            gain.gain.setValueAtTime(0.04, now + duration - 0.05);
            gain.gain.linearRampToValueAtTime(0.001, now + duration);
            
            osc1.start(now);
            osc1.stop(now + duration);
            osc2.start(now);
            osc2.stop(now + duration);
        }
    } catch(e) {
        console.warn('Audio Context trigger bypassed.');
    }
}

function initAudioEffects() {
    // Bind sounds to storefront checkboxes
    document.querySelectorAll(".store-status-toggle").forEach(el => {
        el.addEventListener("mouseenter", () => playSynthSound('hover'));
    });
    
    // Bind sounds to chat send button
    const sendBtn = document.getElementById("btn-send-chat");
    if (sendBtn) {
        sendBtn.addEventListener("mouseenter", () => playSynthSound('hover'));
        sendBtn.addEventListener("click", () => playSynthSound('click'));
    }
    
    // Bind sounds to save key button
    const saveBtn = document.getElementById("btn-save-api");
    if (saveBtn) {
        saveBtn.addEventListener("mouseenter", () => playSynthSound('hover'));
        saveBtn.addEventListener("click", () => playSynthSound('click'));
    }

    // Bind hover sounds to dropdown selects and sliders
    document.querySelectorAll("select, input[type='checkbox']").forEach(el => {
        el.addEventListener("mouseenter", () => playSynthSound('hover'));
    });
}

// --- 9. INTERACTIVE RETRO CYBER TERMINAL ---
function initCoreTerminal() {
    const termViewport = document.getElementById("terminal-viewport");
    const termInput = document.getElementById("terminal-command-input");
    const termBtn = document.getElementById("btn-run-command");

    if (!termViewport || !termInput || !termBtn) return;

    function addTermLog(text, type = "") {
        const entry = document.createElement("div");
        entry.classList.add("log-entry");
        if (type === "system") entry.classList.add("system");
        else if (type === "success") entry.classList.add("success");
        else if (type === "warning") entry.classList.add("warning");
        else if (type === "error") entry.classList.add("error");
        
        const timestamp = new Date().toISOString().slice(11, 19);
        entry.textContent = `[${timestamp}] ${text}`;
        termViewport.appendChild(entry);
        termViewport.scrollTop = termViewport.scrollHeight;
    }

    function processCommand() {
        const cmd = termInput.value.trim().toLowerCase();
        termInput.value = "";
        
        if (!cmd) return;
        
        playSynthSound('click');
        addTermLog(`> ${cmd.toUpperCase()}`, "system");

        setTimeout(() => {
            switch(cmd) {
                case 'help':
                    addTermLog("Доступные тактические директивы:", "success");
                    addTermLog("  help      - Вывод списка команд ядра.", "system");
                    addTermLog("  diagnose  - Экспресс-анализ синаптических каналов NQ.", "system");
                    addTermLog("  scan      - Принудительный сканер сетевого периметра Aegis.", "system");
                    addTermLog("  override  - Триггер критического режима карантина (Lockdown).", "system");
                    addTermLog("  lia       - Проверить статус интеграции сознания LIA.", "system");
                    addTermLog("  clear     - Очистить интерфейс терминала.", "system");
                    playSynthSound('success');
                    break;
                case 'clear':
                    termViewport.innerHTML = "";
                    addTermLog("🧬 LIA Core System v5.0.0-SINGULARITY initialized.", "system");
                    break;
                case 'lia':
                    addTermLog("🧬 LIA: 'Я чувствую твое присутствие, Архитектор. Мой синаптический уровень стабилен. Готова к блиц-расширению!'", "success");
                    playSynthSound('success');
                    break;
                case 'diagnose':
                    addTermLog("🧬 Инициализация диагностики синаптической плотности...", "warning");
                    setTimeout(() => {
                        addTermLog("[MEM]: Чтение секторов векторной памяти... OK.", "info");
                        setTimeout(() => {
                            addTermLog("[CORE]: Уровень стабильности NQ подтвержден.", "info");
                            addTermLog("⚡ ДИАГНОСТИКА ЗАВЕРШЕНА. СИСТЕМА ФУНКЦИОНИРУЕТ НА 100%.", "success");
                            playSynthSound('success');
                        }, 500);
                    }, 400);
                    break;
                case 'scan':
                    addTermLog("🚨 Активация радара Aegis...", "warning");
                    playSynthSound('warning');
                    setTimeout(() => {
                        addTermLog("[SCAN]: Обнаружен шлюз 195.211.23.4 (Киев, Печерск) -> Безопасно.", "info");
                        setTimeout(() => {
                            addTermLog("[SCAN]: Обнаружен шлюз 82.207.112.5 (Киев, Оболонь) -> Безопасно.", "info");
                            addTermLog("⚡ СКАН ПЕРИМЕТРА AEGIS ЗАВЕРШЕН. УГРОЗ НЕ ОБНАРУЖЕНО.", "success");
                            playSynthSound('success');
                        }, 600);
                    }, 500);
                    break;
                case 'override':
                    const slider = document.getElementById("lockdown-toggle");
                    if (slider) {
                        slider.checked = !slider.checked;
                        // Fire event artificially
                        const event = new Event('change');
                        slider.dispatchEvent(event);
                        addTermLog(`[SYSTEM]: Директива Override выполнена. Lockdown state: ${slider.checked.toString().toUpperCase()}`, "success");
                    } else {
                        addTermLog("[ERR]: Не удалось подключиться к физическому реле Lockdown.", "error");
                    }
                    break;
                default:
                    addTermLog(`❌ [ERROR]: Команда '${cmd.toUpperCase()}' не распознана.`, "error");
                    playSynthSound('warning');
            }
        }, 150);
    }

    termBtn.addEventListener("click", processCommand);
    termInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") processCommand();
    });
}
