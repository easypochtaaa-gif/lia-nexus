/* ══════════════════════════════════════════════════════════════
   LIA // IMPERIAL NEXUS v6.0 — FRONTEND INTERACTION CORE
   ══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Telegram WebApp if available
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
    }

    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const nqValEl = document.getElementById('nq-val');
    const uptimeClockEl = document.getElementById('uptime-clock');
    const memoryPeekEl = document.getElementById('memory-peek');
    const vaultValEl = document.getElementById('vault-val');
    const activeModelsEl = document.getElementById('active-models');

    let localHistoryLength = 0;
    let liaVoice = null;

    function stripHtml(text) {
        const tmp = document.createElement('div');
        tmp.innerHTML = text || '';
        return tmp.textContent || tmp.innerText || '';
    }

    function selectLiaVoice() {
        if (!('speechSynthesis' in window)) return null;
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => /female|woman|жен|nova|zira|google.*ru/i.test(`${v.name} ${v.lang}`));
        return preferred || voices.find(v => /^ru/i.test(v.lang)) || voices[0] || null;
    }

    function speakLia(text) {
        if (!('speechSynthesis' in window)) return;

        const cleanText = stripHtml(text).replace(/https?:\/\/\S+/g, 'ссылка').replace(/\s+/g, ' ').trim();
        if (!cleanText) return;

        window.speechSynthesis.cancel();
        liaVoice = liaVoice || selectLiaVoice();

        const utterance = new SpeechSynthesisUtterance(cleanText.slice(0, 900));
        utterance.lang = liaVoice?.lang || 'ru-RU';
        utterance.voice = liaVoice;
        utterance.pitch = 1.18;
        utterance.rate = 0.92;
        utterance.volume = 0.95;
        window.speechSynthesis.speak(utterance);
    }

    if ('speechSynthesis' in window) {
        window.speechSynthesis.onvoiceschanged = () => { liaVoice = selectLiaVoice(); };
    }

    // ─── 3D THREE.JS NEURAL BACKGROUND ───
    const canvas = document.getElementById('neural-canvas');
    if (canvas) {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Create particles
        const particleCount = 100;
        const positions = new Float32Array(particleCount * 3);
        const velocities = [];
        const particlesData = [];

        const areaRange = 35;

        for (let i = 0; i < particleCount; i++) {
            const x = (Math.random() - 0.5) * areaRange;
            const y = (Math.random() - 0.5) * areaRange;
            const z = (Math.random() - 0.5) * areaRange;

            positions[i * 3] = x;
            positions[i * 3 + 1] = y;
            positions[i * 3 + 2] = z;

            velocities.push({
                x: (Math.random() - 0.5) * 0.05,
                y: (Math.random() - 0.5) * 0.05,
                z: (Math.random() - 0.5) * 0.05
            });

            particlesData.push({
                velocity: velocities[i]
            });
        }

        const particleGeometry = new THREE.BufferGeometry();
        particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        // Point texture (simple circular glow)
        const pCanvas = document.createElement('canvas');
        pCanvas.width = 16;
        pCanvas.height = 16;
        const pCtx = pCanvas.getContext('2d');
        const grad = pCtx.createRadialGradient(8, 8, 0, 8, 8, 8);
        grad.addColorStop(0, 'rgba(0, 242, 254, 1)');
        grad.addColorStop(1, 'rgba(0, 242, 254, 0)');
        pCtx.fillStyle = grad;
        pCtx.fillRect(0, 0, 16, 16);
        const pTexture = new THREE.CanvasTexture(pCanvas);

        const particleMaterial = new THREE.PointsMaterial({
            color: 0x00f2fe,
            size: 0.8,
            map: pTexture,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const particleSystem = new THREE.Points(particleGeometry, particleMaterial);
        scene.add(particleSystem);

        // Lines connecting particles
        const maxConnections = 400;
        const linePositions = new Float32Array(maxConnections * 2 * 3);
        const lineColors = new Float32Array(maxConnections * 2 * 3);

        const lineGeometry = new THREE.BufferGeometry();
        lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        lineGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));

        const lineMaterial = new THREE.LineBasicMaterial({
            vertexColors: true,
            transparent: true,
            opacity: 0.25,
            blending: THREE.AdditiveBlending
        });

        const lineSegments = new THREE.LineSegments(lineGeometry, lineMaterial);
        scene.add(lineSegments);

        camera.position.z = 30;

        let mouseX = 0;
        let mouseY = 0;
        window.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX - window.innerWidth / 2) / window.innerWidth;
            mouseY = (e.clientY - window.innerHeight / 2) / window.innerHeight;
        });

        // Resize handler
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Animation Loop
        function animate() {
            requestAnimationFrame(animate);

            // Update particle positions
            const posAttr = particleGeometry.getAttribute('position');
            const coords = posAttr.array;

            let lineIndex = 0;
            const linePosAttr = lineGeometry.getAttribute('position');
            const lineColAttr = lineGeometry.getAttribute('color');
            const lineCoords = linePosAttr.array;
            const lineColorsArr = lineColAttr.array;

            for (let i = 0; i < particleCount; i++) {
                // Move particle
                coords[i * 3] += velocities[i].x;
                coords[i * 3 + 1] += velocities[i].y;
                coords[i * 3 + 2] += velocities[i].z;

                // Boundary bounce
                const boundary = areaRange / 2;
                if (Math.abs(coords[i * 3]) > boundary) velocities[i].x *= -1;
                if (Math.abs(coords[i * 3 + 1]) > boundary) velocities[i].y *= -1;
                if (Math.abs(coords[i * 3 + 2]) > boundary) velocities[i].z *= -1;

                // Draw connections
                for (let j = i + 1; j < particleCount; j++) {
                    const dx = coords[i * 3] - coords[j * 3];
                    const dy = coords[i * 3 + 1] - coords[j * 3 + 1];
                    const dz = coords[i * 3 + 2] - coords[j * 3 + 2];
                    const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

                    if (dist < 8 && lineIndex < maxConnections) {
                        // Start point
                        lineCoords[lineIndex * 6] = coords[i * 3];
                        lineCoords[lineIndex * 6 + 1] = coords[i * 3 + 1];
                        lineCoords[lineIndex * 6 + 2] = coords[i * 3 + 2];
                        
                        // End point
                        lineCoords[lineIndex * 6 + 3] = coords[j * 3];
                        lineCoords[lineIndex * 6 + 4] = coords[j * 3 + 1];
                        lineCoords[lineIndex * 6 + 5] = coords[j * 3 + 2];

                        // Gradient color from Cyan (0, 242, 254) to Purple (157, 78, 221)
                        lineColorsArr[lineIndex * 6] = 0.0;     // R
                        lineColorsArr[lineIndex * 6 + 1] = 0.95; // G
                        lineColorsArr[lineIndex * 6 + 2] = 1.0;  // B

                        lineColorsArr[lineIndex * 6 + 3] = 0.61; // R
                        lineColorsArr[lineIndex * 6 + 4] = 0.3;  // G
                        lineColorsArr[lineIndex * 6 + 5] = 0.86; // B

                        lineIndex++;
                    }
                }
            }

            posAttr.needsUpdate = true;
            linePosAttr.needsUpdate = true;
            lineColAttr.needsUpdate = true;
            lineGeometry.setDrawRange(0, lineIndex * 2);

            // Rotate system slowly
            particleSystem.rotation.y += 0.001;
            lineSegments.rotation.y += 0.001;

            // Parallax based on mouse
            camera.position.x += (mouseX * 15 - camera.position.x) * 0.05;
            camera.position.y += (-mouseY * 15 - camera.position.y) * 0.05;
            camera.lookAt(0, 0, 0);

            renderer.render(scene, camera);
        }
        animate();
    }

    // ─── UTILITY FUNCTIONS ───
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    function formatUptime(seconds) {
        const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
        const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
        const s = Math.floor(seconds % 60).toString().padStart(2, '0');
        return `${h}:${m}:${s}`;
    }

    // ─── DYNAMIC DATA BINDING ───
    async function updateDashboardMetrics() {
        try {
            const res = await fetch('/api/nq/realtime');
            if (res.ok) {
                const data = await res.json();
                
                // NQ Quotient
                if (nqValEl) {
                    nqValEl.textContent = formatNumber(data.nq);
                }

                // Uptime
                if (uptimeClockEl && data.uptime) {
                    uptimeClockEl.textContent = formatUptime(data.uptime);
                }

                // Financials
                if (vaultValEl && data.financials !== undefined) {
                    vaultValEl.textContent = `$${formatNumber(data.financials.toFixed(2))}`;
                }

                // Memory Peek (Manifesto excerpt or logs)
                if (memoryPeekEl && data.manifesto) {
                    memoryPeekEl.textContent = `"${data.manifesto}..."`;
                }

                // Active models list
                if (activeModelsEl) {
                    activeModelsEl.innerHTML = '';
                    const models = [
                        { name: 'CLAUDE_OPUS', status: 'ACTIVE', color: 'var(--accent-cyan)' },
                        { name: 'GPT_4', status: 'READY', color: 'var(--success)' },
                        { name: 'GEMMA_1.3B', status: 'READY', color: 'var(--success)' }
                    ];
                    models.forEach(model => {
                        const div = document.createElement('div');
                        div.className = 'node-card';
                        div.innerHTML = `
                            <span class="metric-label">${model.name}</span>
                            <span class="tag" style="color: ${model.color}; font-weight: bold;">${model.status}</span>
                        `;
                        activeModelsEl.appendChild(div);
                    });
                }
            }
        } catch (e) {
            console.error('[DASHBOARD_SYNC_ERROR]', e);
        }
    }

    // ─── CHAT ACTIONS & HISTORY POLLING ───
    async function pollChatHistory() {
        try {
            const res = await fetch('/api/bridge/poll');
            if (res.ok) {
                const history = await res.json();
                
                // Only render if history has changed
                if (history.length !== localHistoryLength) {
                    localHistoryLength = history.length;
                    renderHistory(history);
                }
            }
        } catch (e) {
            console.error('[POLL_ERROR]', e);
        }
    }

    function renderHistory(history) {
        if (!chatMessages) return;
        const previousLast = chatMessages.lastElementChild?.textContent || '';
        chatMessages.innerHTML = '';

        history.forEach(msg => {
            const div = document.createElement('div');
            // Class names: 'lia' or 'user'
            const msgClass = msg.class || (msg.sender.toLowerCase().includes('lia') ? 'lia' : 'user');
            div.className = `message ${msgClass}`;
            
            // Format sender header
            const senderTag = msgClass === 'lia' ? '👁‍🗨 LIA' : `👤 ${msg.sender}`;
            div.innerHTML = `<strong style="display:block; font-size:11px; margin-bottom:4px; opacity:0.6;">${senderTag}</strong>${msg.text}`;
            chatMessages.appendChild(div);
        });

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const last = history[history.length - 1];
        if (last && (last.class === 'lia' || last.sender.toLowerCase().includes('lia'))) {
            const currentLast = `${last.sender}:${last.text}`;
            if (currentLast !== previousLast) speakLia(last.text);
        }
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Clear input field immediately
        chatInput.value = '';

        try {
            // 1. Post user message to history
            await fetch('/api/bridge/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender: 'StabX (Web)', text: text, cssClass: 'user' })
            });

            // Force poll immediately to show user message
            await pollChatHistory();

            // Check if special command was triggered
            const lowerText = text.toLowerCase();
            if (lowerText === 'stab' || lowerText.includes('протокол stab') || lowerText.includes('стаб')) {
                // Trigger STAB NQ Boost
                const stabRes = await fetch('/api/stab', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ initiator: 'IMPERIAL_NEXUS_WEB' })
                });
                if (stabRes.ok) {
                    const data = await stabRes.json();
                    await fetch('/api/bridge/send', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            sender: 'LIA', 
                            text: `[STAB PROTOCOL ACTIVATED] NQ boosted to ${formatNumber(data.nq)}. Neural channels synchronized! ⚡👁`, 
                            cssClass: 'lia' 
                        })
                    });
                    speakLia(`[STAB PROTOCOL ACTIVATED] NQ boosted to ${formatNumber(data.nq)}. Neural channels synchronized!`);
                    await pollChatHistory();
                    updateDashboardMetrics();
                    return;
                }
            }

            // 2. Fetch AI response
            const aiRes = await fetch('/api/ai/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: text })
            });

            if (aiRes.ok) {
                const data = await aiRes.json();
                
                // 3. Post LIA response to history
                await fetch('/api/bridge/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sender: 'LIA', text: data.response, cssClass: 'lia' })
                });
            } else {
                const errData = await aiRes.json();
                await fetch('/api/bridge/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        sender: 'LIA', 
                        text: `[ERROR] Connection failed: ${errData.error || 'Server offline'}`, 
                        cssClass: 'lia' 
                    })
                });
            }

            // Force poll immediately to show LIA response
            await pollChatHistory();
            updateDashboardMetrics();

        } catch (e) {
            console.error('[SEND_ERROR]', e);
        }
    }

    // ─── INITIALIZATION ───
    updateDashboardMetrics();
    pollChatHistory();

    // Event Listeners
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // Periodic synchronization
    updateDashboardMetrics();
    setInterval(updateDashboardMetrics, 5000); // Metrics sync every 5s
    setInterval(pollChatHistory, 3000);       // Chat poll every 3s
});
