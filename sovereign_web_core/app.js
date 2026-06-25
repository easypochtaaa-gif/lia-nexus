/* --- LIA SOVEREIGN CORE APP ORCHESTRATOR --- */

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initClockAndUptime();
    initNeuralCanvas();
    initLoadSimulators(); loadStats();
    initAegisScanner();
    initChatInterface();
    initStorefrontToggles();
    initCoreTerminal();
    initAudioEffects();
    initWeb3();
    initQuests();
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

            if (targetTab === 'tab-quest-moderation') {
                loadAdminQuests();
                startStreamMonitor();
            } else {
                stopStreamMonitor();
            }
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

// --- 5. LOAD STATS INTO DASHBOARD ---
function loadStats() {
    // Placeholder values (напуском) – replace with real API calls later
    const uptimeElem = document.getElementById('uptime-counter');
    const threatsElem = document.getElementById('threats-blocked');
    const activeUsersElem = document.getElementById('active-users-stat');
    const vipUsersElem = document.getElementById('vip-users-trend');

    // Fetch real stats from server
    fetch('/api/stats')
      .then(r => r.json())
      .then(data => {
          if (uptimeElem) uptimeElem.textContent = data.uptime || '148ч';
          if (threatsElem) threatsElem.textContent = `${data.threats_blocked || 0}`;
          if (activeUsersElem) activeUsersElem.textContent = `${data.total_users || 0}`;
          if (vipUsersElem) vipUsersElem.textContent = `${data.vip_users || 0}`;
      })
      .catch(() => {
          // Fallback if API unavailable
          if (uptimeElem) uptimeElem.textContent = '…';
          if (threatsElem) threatsElem.textContent = '…';
          if (activeUsersElem) activeUsersElem.textContent = '…';
          if (vipUsersElem) vipUsersElem.textContent = '…';
      });
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

    // Chat is ALWAYS enabled now — backend handles API keys
    // API key field is kept for backward compatibility (optional override)
    const savedKey = localStorage.getItem("sovereign_api_key");
    if (savedKey) {
        apiInput.value = savedKey;
    }
    enableChat(true);  // Always enabled

    saveBtn.addEventListener("click", () => {
        const key = apiInput.value.trim();
        if (key) {
            localStorage.setItem("sovereign_api_key", key);
            alert("🔑 Ключ сохранён локально (опционально).");
        } else {
            localStorage.removeItem("sovereign_api_key");
        }
    });

    function enableChat(enable) {
        chatInput.disabled = !enable;
        sendBtn.disabled = !enable;
        if (enable) {
            chatInput.placeholder = "Введите ваш запрос к Лие... (или нажмите 🎤 для голоса)";
        }
    }

    // Get or create web user ID (stored in localStorage)
    function getWebUserId() {
        let uid = localStorage.getItem("lia_web_user_id");
        if (!uid) {
            uid = "web_" + Math.random().toString(36).substring(2, 10);
            localStorage.setItem("lia_web_user_id", uid);
        }
        return uid;
    }

    async function sendPrompt() {
        const prompt = chatInput.value.trim();

        if (!prompt) return;

        // Append user message to UI
        appendMessage(prompt, "user");
        chatInput.value = "";

        // Disable inputs
        chatInput.disabled = true;
        sendBtn.disabled = true;
        typingIndicator.style.display = "block";
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const webSearch = webSearchToggle ? webSearchToggle.checked : false;
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: prompt,
                    user_id: getWebUserId(),
                    web_search: webSearch
                })
            });

            const data = await response.json();
            typingIndicator.style.display = "none";

            if (response.ok && data.reply) {
                appendMessage(data.reply, "bot");
                // TTS: speak the response
                speakResponse(data.reply);
            } else if (response.ok && data.content && data.content[0]) {
                // Fallback: raw Anthropic format (if server still in proxy mode)
                const responseText = data.content[0].text;
                appendMessage(responseText, "bot");
                speakResponse(responseText);
            } else {
                const errMsg = data.error || "Неизвестная ошибка нейро-ядра.";
                appendMessage(`❌ ${errMsg}`, "bot");
            }
        } catch (error) {
            typingIndicator.style.display = "none";
            appendMessage(`❌ Сбой сетевого моста: ${error.message}`, "bot");
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

    // ── Voice Input (Web Speech API) ──
    initVoiceInput();
}

// --- VOICE INPUT + TTS ─────────────────────────────────────
function initVoiceInput() {
    const micBtn = document.getElementById("btn-voice-input");
    const chatInput = document.getElementById("chat-prompt-input");
    const voiceStatus = document.getElementById("voice-status-indicator");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        if (micBtn) micBtn.style.display = "none";
        console.log("[LIA] Web Speech API not available — voice input disabled.");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "ru-RU";
    recognition.continuous = false;
    recognition.interimResults = false;

    let isListening = false;

    recognition.onstart = () => {
        isListening = true;
        if (voiceStatus) voiceStatus.style.display = "block";
        if (micBtn) micBtn.innerHTML = '<span class="mic-icon">⏹️</span>';
        if (micBtn) micBtn.classList.add("listening");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (chatInput) chatInput.value = transcript;
        if (voiceStatus) voiceStatus.style.display = "none";
        if (micBtn) micBtn.innerHTML = '<span class="mic-icon">🎤</span>';
        if (micBtn) micBtn.classList.remove("listening");
        isListening = false;
        // Auto-send after voice input
        if (transcript.trim()) {
            const sendBtn = document.getElementById("btn-send-chat");
            if (sendBtn) sendBtn.click();
        }
    };

    recognition.onerror = (event) => {
        console.error("[LIA] Voice recognition error:", event.error);
        if (voiceStatus) {
            voiceStatus.textContent = "❌ Ошибка: " + event.error + ". Попробуйте ещё раз.";
            voiceStatus.style.display = "block";
            setTimeout(() => { if (voiceStatus) voiceStatus.style.display = "none"; }, 3000);
        }
        if (micBtn) micBtn.innerHTML = '<span class="mic-icon">🎤</span>';
        if (micBtn) micBtn.classList.remove("listening");
        isListening = false;
    };

    recognition.onend = () => {
        if (micBtn) micBtn.innerHTML = '<span class="mic-icon">🎤</span>';
        if (micBtn) micBtn.classList.remove("listening");
        if (!isListening && voiceStatus) voiceStatus.style.display = "none";
    };

    if (micBtn) {
        micBtn.addEventListener("click", () => {
            if (isListening) {
                recognition.stop();
                isListening = false;
            } else {
                try {
                    recognition.start();
                } catch (e) {
                    console.error("[LIA] Failed to start recognition:", e);
                }
            }
        });
    }

    console.log("[LIA] Voice input initialized (ru-RU).");
}

function speakResponse(text) {
    if (!window.speechSynthesis) return;

    // Strip markdown-like formatting for cleaner speech
    let cleanText = text
        .replace(/\*\*/g, "")
        .replace(/\*/g, "")
        .replace(/`/g, "")
        .replace(/\[/g, "")
        .replace(/\]/g, "")
        .replace(/\(/g, "")
        .replace(/\)/g, "");

    // Truncate long responses for speech
    if (cleanText.length > 500) {
        cleanText = cleanText.substring(0, 500) + "...";
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "ru-RU";
    utterance.rate = 1.05;
    utterance.pitch = 1.1;
    utterance.volume = 0.9;

    // Try to find a female Russian voice
    const voices = speechSynthesis.getVoices();
    const ruVoices = voices.filter(v => v.lang.startsWith("ru"));
    const femaleVoice = ruVoices.find(v => v.name.includes("Female") || v.name.includes("Katya") || v.name.includes("Milena"));
    if (femaleVoice) {
        utterance.voice = femaleVoice;
    } else if (ruVoices.length > 0) {
        utterance.voice = ruVoices[0];
    }

    speechSynthesis.speak(utterance);
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

// --- 10. WEB3 WALLET CONNECTION ---
function initWeb3() {
    const connectBtn = document.getElementById("btn-connect-wallet");
    const addressDisplay = document.getElementById("wallet-address");

    if (!connectBtn) return;

    connectBtn.addEventListener("click", async () => {
        playSynthSound('click');
        try {
            let account = null;
            if (window.ethereum) {
                // MetaMask or compatible EVM wallet
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                account = accounts[0];
            } else if (window.solana && window.solana.isPhantom) {
                // Phantom Wallet
                const response = await window.solana.connect();
                account = response.publicKey.toString();
            } else {
                alert("Web3 кошелек (MetaMask или Phantom) не обнаружен. Пожалуйста, установите расширение.");
                return;
            }

            if (account) {
                addressDisplay.textContent = account.slice(0, 12) + '...';
                addressDisplay.style.display = "block";
                connectBtn.textContent = "🔗 CONNECTED";
                connectBtn.classList.add("wallet-connected");
                playSynthSound('success');

                // If running in Telegram WebApp, send data back to the bot
                if (window.Telegram && window.Telegram.WebApp) {
                    window.Telegram.WebApp.sendData(JSON.stringify({
                        action: "wallet_connect",
                        wallet: account
                    }));
                }

                // Also save to server via API (works both in WebView and browser)
                try {
                    const uid = getWebUserId();
                    await fetch('/api/connect-wallet', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: uid, wallet: account })
                    });
                    console.log('[WEB3] Wallet saved to server:', account.slice(0, 12) + '...');
                } catch (apiErr) {
                    console.error('[WEB3] Failed to save wallet to server:', apiErr);
                }
            }
        } catch (error) {
            console.error(error);
            alert("Ошибка при подключении кошелька: " + error.message);
        }
    });
}

// --- 11. QUESTS & LEADERBOARD ---
function initQuests() {
    const questsList = document.getElementById("quests-list");
    const leaderboardList = document.getElementById("leaderboard-list");

    if (!questsList || !leaderboardList) return;

    // Dummy Quests Data
    const quests = [
        { title: "Подключить Кошелек", desc: "Свяжите Web3 кошелек (MetaMask/Phantom) с профилем.", reward: "500 STAB", status: "Активно" },
        { title: "Первый Контакт", desc: "Проведите первую диалоговую сессию с разумом LIA.", reward: "250 XP", status: "Выполнено" },
        { title: "Пригласить Рекрута", desc: "Пригласите 1 друга в Империю по вашей реферальной ссылке.", reward: "1000 STAB", status: "Активно" }
    ];

    // Dummy Leaderboard Data
    const leaderboard = [
        { rank: 1, name: "Architect", score: "999,999 XP" },
        { rank: 2, name: "CyberNinja", score: "45,230 XP" },
        { rank: 3, name: "NeonPhantom", score: "38,100 XP" },
        { rank: 4, name: "NullPointer", score: "12,050 XP" },
        { rank: 5, name: "GhostProtocol", score: "8,900 XP" }
    ];

    // Render Quests
    questsList.innerHTML = quests.map(q => `
        <div class="store-card ${q.status === 'Выполнено' ? 'offline' : 'online'}" style="margin-bottom: 10px; padding: 15px;">
            <div class="store-card-header">
                <span class="store-status-badge">${q.status}</span>
                <span class="store-location" style="color: var(--accent-cyan); font-weight: bold;">Награда: ${q.reward}</span>
            </div>
            <h2 class="store-title" style="font-size: 1.1rem; margin-bottom: 5px;">${q.title}</h2>
            <div class="store-details" style="font-size: 0.85rem; color: #a1a1aa;">${q.desc}</div>
        </div>
    `).join('');

    // Render Leaderboard
    leaderboardList.innerHTML = leaderboard.map(l => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid rgba(168,85,247,0.2); background: rgba(0,0,0,0.2); margin-bottom: 5px; border-radius: 4px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-family: 'Orbitron'; font-size: 1.2rem; color: ${l.rank === 1 ? 'gold' : l.rank === 2 ? 'silver' : l.rank === 3 ? '#cd7f32' : 'var(--accent-violet)'}; font-weight: bold;">#${l.rank}</span>
                <span style="font-weight: 500;">${l.name}</span>
            </div>
            <span style="font-family: monospace; color: var(--accent-cyan);">${l.score}</span>
        </div>
    `).join('');
}

// --- 12. ADMIN QUEST MODERATION & LIVE STREAM MONITOR ---
let adminStreamUser = "";
let adminStreamTimer = null;

async function loadAdminQuests() {
    const listDiv = document.getElementById("admin-quest-apps-list");
    if (!listDiv) return;

    try {
        const res = await fetch("/api/quests/applications");
        const data = await res.json();
        
        const select = document.getElementById("admin-stream-select");
        const prevValue = select.value;
        select.innerHTML = '<option value="">Нет активных стримов</option>';

        let activeUsers = [];

        listDiv.innerHTML = (data.applications || []).map(a => {
            let statusText = 'На модерации';
            let statusStyle = 'color: var(--accent-gold); font-weight: bold;';
            let actionHTML = '';

            if (a.status === 'completed') {
                statusText = 'Выполнен';
                statusStyle = 'color: var(--accent-green);';
            } else if (a.status === 'active') {
                statusText = 'Выполняется (LIVE)';
                statusStyle = 'color: var(--accent-cyan); font-weight: bold; animation: blink 1.2s infinite;';
                activeUsers.push({ id: a.user_id, name: a.user_name });
            } else if (a.status === 'approved') {
                statusText = 'Условия выставлены';
                statusStyle = 'color: var(--accent-purple);';
            } else if (a.status === 'pending') {
                actionHTML = `
                    <div style="margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                        <label style="font-size: 11px; display: block; margin-bottom: 4px;">ВЫСТАВИТЬ УСЛОВИЯ КВЕСТА:</label>
                        <textarea id="conditions-${a.id}" class="cyber-input" style="height: 60px; font-family: inherit; margin-bottom: 8px;" placeholder="Например: Сделать селфи на локации и стримить не менее 3 минут"></textarea>
                        <button onclick="approveQuest(${a.id})" class="cyber-button" style="padding: 6px 12px; font-size: 11px;">ОДОБРИТЬ ЗАЯВКУ</button>
                    </div>
                `;
            }

            return `
                <div class="store-card online" style="margin-bottom: 12px; padding: 16px; border: 1px solid rgba(168,85,247,0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 11px; color: var(--accent-cyan);">Игрок: <b>${a.user_name} (ID: ${a.user_id})</b></span>
                        <span style="font-size: 11px; ${statusStyle}">${statusText}</span>
                    </div>
                    <h4 style="font-family: Orbitron, sans-serif; font-size: 1.1rem; margin-bottom: 6px;">${a.title}</h4>
                    <p style="font-size: 12px; color: var(--text-dim); line-height: 1.4;">${a.description}</p>
                    ${a.conditions ? `<p style="font-size: 12px; color: var(--accent-purple); margin-top: 6px;"><b>Условия LIA:</b> ${a.conditions}</p>` : ''}
                    ${actionHTML}
                </div>
            `;
        }).join('');

        if (activeUsers.length > 0) {
            activeUsers.forEach(u => {
                select.innerHTML += `<option value="${u.id}">${u.name} (ID: ${u.id})</option>`;
            });
            if (prevValue && activeUsers.find(u => u.id == prevValue)) {
                select.value = prevValue;
            }
        }
    } catch (e) {
        listDiv.innerHTML = `<div class="log-entry error">[ERROR]: Failed to load quest applications: ${e.message}</div>`;
    }
}

async function approveQuest(appId) {
    const textarea = document.getElementById(`conditions-${appId}`);
    const conditions = textarea ? textarea.value.trim() : "";
    
    if (!conditions) {
        alert("Пожалуйста, введите условия квеста для игрока.");
        return;
    }

    try {
        const res = await fetch("/api/quests/approve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ application_id: appId, conditions: conditions })
        });
        const data = await res.json();
        if (data.success) {
            alert("Заявка одобрена, условия отправлены игроку!");
            loadAdminQuests();
        }
    } catch (e) {
        alert("Ошибка одобрения: " + e.message);
    }
}

function changeActiveStreamUser() {
    const select = document.getElementById("admin-stream-select");
    adminStreamUser = select ? select.value : "";
    
    const liveLabel = document.getElementById("admin-stream-live-label");
    const streamImg = document.getElementById("admin-stream-img");
    const placeholder = document.getElementById("admin-stream-placeholder");

    if (!adminStreamUser) {
        liveLabel.textContent = "OFFLINE";
        liveLabel.style.background = "#ef4444";
        streamImg.style.display = "none";
        placeholder.style.display = "flex";
    } else {
        liveLabel.textContent = "LIVE";
        liveLabel.style.background = "#10b981";
        streamImg.style.display = "block";
        placeholder.style.display = "none";
    }
}

function startStreamMonitor() {
    stopStreamMonitor();
    
    adminStreamTimer = setInterval(async () => {
        if (!adminStreamUser) return;
        
        try {
            const res = await fetch(`/api/quests/get-stream-frame?user_id=${adminStreamUser}`);
            const data = await res.json();
            
            const img = document.getElementById("admin-stream-img");
            if (data.frame && img) {
                img.src = data.frame;
            }
        } catch (e) {
            console.error("Failed to fetch stream frame:", e);
        }
    }, 1500);
}

function stopStreamMonitor() {
    if (adminStreamTimer) {
        clearInterval(adminStreamTimer);
        adminStreamTimer = null;
    }
}
