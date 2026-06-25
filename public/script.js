document.addEventListener('DOMContentLoaded', () => {
    // --- Telegram Web App Setup ---
    let tg = null;
    let userId = 7915004877; // Default Master ID
    let userName = 'Юнит';

    if (window.Telegram && window.Telegram.WebApp) {
        tg = window.Telegram.WebApp;
        tg.expand();
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            userId = tg.initDataUnsafe.user.id;
            userName = tg.initDataUnsafe.user.first_name || 'Юнит';
        }
        console.log(`[TMA] Initialized with User ID: ${userId}, Name: ${userName}`);
    }

    // --- State Management ---
    let state = {
        nq: 100000,
        stage: 'seed',
        rubBalance: 0,
        stabaxBalance: 50,
        referralCount: 0,
        activeTab: 'tab-chat',
        selectedCountry: 'russia',
        selectedService: null,
        activeOrder: null, // { id, phone, product, country, price }
        isPlaying: false,
        activeTrack: 'anthem'
    };

    // Load active order from localStorage if exists
    const savedOrder = localStorage.getItem('lia_active_order');
    if (savedOrder) {
        state.activeOrder = JSON.parse(savedOrder);
    }

    // --- Elements ---
    const clockEl = document.getElementById('clock');
    const headerBalance = document.getElementById('header-balance');
    const balanceLabel = document.getElementById('balance-label');
    const connectionStatus = document.getElementById('connection-status');
    const settingsBtn = document.getElementById('settings-btn');
    const apiModal = document.getElementById('api-modal');
    const apiKeyInput = document.getElementById('api-key-input');
    const saveKeyBtn = document.getElementById('save-key-btn');
    const skipKeyBtn = document.getElementById('skip-key-btn');

    // Bottom Navigation
    const navItems = document.querySelectorAll('.bottom-nav .nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    // Chat Tab Elements
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const ghostContainer = document.getElementById('ghost-container');

    // SMS Tab Elements
    const activeOrderScreen = document.getElementById('active-order-screen');
    const smsStoreSelection = document.getElementById('sms-store-selection');
    const countryButtons = document.querySelectorAll('.country-btn');
    const serviceButtons = document.querySelectorAll('.service-btn');
    const buyNumberBtn = document.getElementById('buy-number-btn');
    const orderPhone = document.getElementById('order-phone');
    const orderService = document.getElementById('order-service');
    const orderCountry = document.getElementById('order-country');
    const orderCode = document.getElementById('order-code');
    const orderSmsText = document.getElementById('order-sms-text');
    const checkSmsBtn = document.getElementById('check-sms-btn');
    const cancelOrderBtn = document.getElementById('cancel-order-btn');
    const finishOrderBtn = document.getElementById('finish-order-btn');

    // Wallet Tab Elements
    const stabaxBalanceEl = document.getElementById('stabax-balance');
    const refCountText = document.getElementById('ref-count-text');
    const referralLinkInput = document.getElementById('referral-link-input');
    const copyRefBtn = document.getElementById('copy-ref-btn');

    // Swarm Tab Elements
    const nqTextTab = document.getElementById('nq-text-tab');
    const nqProgressTab = document.getElementById('nq-progress-tab');
    const evolutionStageTab = document.getElementById('evolution-stage-tab');
    const metricUsers = document.getElementById('metric-users');
    const metricQuests = document.getElementById('metric-quests');
    const agentsListTarget = document.getElementById('agents-list-target');

    // Music Tab Elements
    const musicVisualizer = document.getElementById('music-visualizer');
    const musicSphere = document.getElementById('music-sphere');
    const musicTrackTitle = document.getElementById('music-track-title');
    const musicTrackStyle = document.getElementById('music-track-style');
    const musicPlayBtn = document.getElementById('music-play-btn');
    const musicPrevBtn = document.getElementById('music-prev-btn');
    const musicNextBtn = document.getElementById('music-next-btn');
    const playlistItems = document.querySelectorAll('.playlist-item');

    // Canvas Background
    const bgCanvas = document.getElementById('neural-canvas');

    // --- Clock ---
    if (clockEl) {
        setInterval(() => {
            clockEl.textContent = new Date().toTimeString().split(' ')[0];
        }, 1000);
    }

    // --- Tab Switching ---
    function switchTab(tabId) {
        if (tg) tg.HapticFeedback.impactOccurred('light');

        state.activeTab = tabId;
        
        navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.tab === tabId);
        });

        tabContents.forEach(tab => {
            tab.classList.toggle('active', tab.id === tabId);
        });

        // Update top header balance display depending on active tab
        updateHeaderBalance();

        // Specific tab load actions
        if (tabId === 'tab-swarm') {
            syncSwarmStatus();
        } else if (tabId === 'tab-wallet') {
            syncWalletStats();
        } else if (tabId === 'tab-sms') {
            syncSmsBalance();
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => switchTab(item.dataset.tab));
    });

    function updateHeaderBalance() {
        if (state.activeTab === 'tab-sms') {
            balanceLabel.textContent = 'БАЛАНС 5SIM';
            headerBalance.textContent = `${state.rubBalance.toFixed(2)} ₽`;
            headerBalance.style.color = 'var(--success)';
        } else {
            balanceLabel.textContent = 'БАЛАНС STABAX';
            headerBalance.textContent = `${state.stabaxBalance.toFixed(0)} STB`;
            headerBalance.style.color = 'var(--accent)';
        }
    }

    // --- API & Sync Functions ---
    async function syncSmsBalance() {
        try {
            const res = await fetch(`/api/user/balance?userId=${userId}`);
            if (res.ok) {
                const data = await res.json();
                state.rubBalance = data.balance;
                updateHeaderBalance();
            }
        } catch (e) {
            console.error('Failed to sync SMS balance:', e);
        }
    }

    async function syncWalletStats() {
        try {
            const res = await fetch(`/api/user/profile?userId=${userId}`);
            if (res.ok) {
                const data = await res.json();
                state.stabaxBalance = data.stabax_balance || 50;
                state.referralCount = data.referral_count || 0;
                
                if (stabaxBalanceEl) stabaxBalanceEl.textContent = state.stabaxBalance.toFixed(2);
                if (refCountText) refCountText.textContent = state.referralCount;
                if (referralLinkInput) referralLinkInput.value = `https://t.me/stab_lia_bot?start=${userId}`;
                
                updateHeaderBalance();
            }
        } catch (e) {
            console.error('Failed to sync wallet stats:', e);
        }
    }

    async function syncSwarmStatus() {
        try {
            // NQ status
            const resStatus = await fetch('/api/status');
            if (resStatus.ok) {
                const data = await resStatus.json();
                state.nq = data.nq;
                state.stage = data.stage;

                if (nqTextTab) nqTextTab.textContent = `${Math.floor(state.nq).toLocaleString()} / 100,000,000`;
                if (evolutionStageTab) evolutionStageTab.textContent = `STAGE: ${state.stage.toUpperCase()}`;
                
                const displayNqPercent = Math.min(100, (state.nq / 100000000) * 100);
                if (nqProgressTab) nqProgressTab.style.width = `${displayNqPercent}%`;

                // procedurally scale stats
                if (metricUsers) metricUsers.textContent = Math.floor(154 + (state.nq / 1000000));
                if (metricQuests) metricQuests.textContent = Math.floor(12 + (state.nq / 5000000));
            }

            // Agents list
            const resAgents = await fetch('/api/agents');
            if (resAgents.ok && agentsListTarget) {
                const data = await resAgents.json();
                agentsListTarget.innerHTML = data.staff.map(agent => `
                    <div class="agent-item-card">
                        <div class="agent-card-top">
                            <span class="agent-card-name">${agent.name}</span>
                            <span class="agent-card-eff">Эффективность: ${Math.floor(agent.efficiency * 100)}%</span>
                        </div>
                        <div class="agent-card-role">Роль: ${agent.role}</div>
                        <div class="agent-card-task">Задача: ${agent.task}</div>
                    </div>
                `).join('');
            }
        } catch (e) {
            console.error('Failed to sync swarm status:', e);
        }
    }

    // --- Copy Buttons ---
    window.copyText = (elementId) => {
        const el = document.getElementById(elementId);
        if (!el) return;
        
        let textToCopy = el.textContent || el.value;
        navigator.clipboard.writeText(textToCopy).then(() => {
            if (tg) {
                tg.HapticFeedback.notificationOccurred('success');
                tg.showPopup({ message: 'Скопировано в буфер обмена!' });
            } else {
                alert('Скопировано!');
            }
        });
    };

    if (copyRefBtn) {
        copyRefBtn.onclick = () => copyText('referral-link-input');
    }

    // --- Chat Interface Logic ---
    function addChatMessage(text, type = 'bot') {
        if (!chatMessages) return;
        const bubble = document.createElement('div');
        bubble.className = `msg-bubble ${type}`;
        bubble.textContent = text;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendChatMessage(text) {
        if (!text) return;
        addChatMessage(text, 'user');
        chatInput.value = '';
        
        // Show typing indicator
        const typing = document.createElement('div');
        typing.className = 'msg-bubble bot typing-indicator';
        typing.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(typing);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, user_id: userId })
            });

            typing.remove();

            if (res.ok) {
                const data = await res.json();
                if (data.reply) {
                    addChatMessage(data.reply, 'bot');
                } else {
                    addChatMessage('Lia: [Связь прервана. Ответ пуст.]', 'bot');
                }
            } else {
                addChatMessage('Lia: [Превышено время ожидания. Повторите попытку.]', 'bot');
            }
        } catch (err) {
            typing.remove();
            addChatMessage('Lia: [Ошибка нейросети. Проверьте туннель.]', 'bot');
        }

        // Procedurally boost NQ slightly on chat activity
        fetch('/api/stab', { method: 'POST' }).then(() => syncWalletStats());
    }

    if (sendBtn) {
        sendBtn.onclick = () => sendChatMessage(chatInput.value.trim());
    }
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage(chatInput.value.trim());
            }
        });
    }

    // Voice recognition (Web Speech API)
    if (micBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'ru-RU';
            recognition.interimResults = false;

            recognition.onstart = () => {
                if (tg) tg.HapticFeedback.impactOccurred('medium');
                micBtn.textContent = '🛑';
                micBtn.style.color = 'var(--danger)';
            };

            recognition.onresult = (event) => {
                const speechResult = event.results[0][0].transcript;
                if (chatInput) chatInput.value = speechResult;
            };

            recognition.onerror = () => {
                micBtn.textContent = '🎤';
                micBtn.style.color = 'var(--text-secondary)';
            };

            recognition.onend = () => {
                micBtn.textContent = '🎤';
                micBtn.style.color = 'var(--text-secondary)';
            };

            micBtn.onclick = () => {
                if (micBtn.textContent === '🎤') {
                    recognition.start();
                } else {
                    recognition.stop();
                }
            };
        } else {
            micBtn.style.display = 'none';
        }
    }

    // Preset replies generator
    function generateGhostReplies() {
        const prompts = [
            "💾 Сохранить SAVEPOINT",
            "📊 Статус NQ",
            "🔥 Разогнать синапсы",
            "🧬 Отчет эволюции"
        ];
        if (!ghostContainer) return;
        ghostContainer.innerHTML = '';
        prompts.sort(() => Math.random() - 0.5).slice(0, 3).forEach(p => {
            const btn = document.createElement('button');
            btn.className = 'ghost-btn';
            btn.textContent = p;
            btn.onclick = () => {
                if (tg) tg.HapticFeedback.impactOccurred('light');
                sendChatMessage(p);
            };
            ghostContainer.appendChild(btn);
        });
    }

    // --- SMS Store Interface Logic ---
    function renderSmsStore() {
        if (state.activeOrder) {
            // Show active order screen
            smsStoreSelection.classList.add('hidden');
            activeOrderScreen.classList.remove('hidden');
            
            orderService.textContent = state.activeOrder.product.toUpperCase();
            orderCountry.textContent = state.activeOrder.country.toUpperCase();
            orderPhone.textContent = state.activeOrder.phone;
            
            // Check localStorage for saved code
            const savedCode = localStorage.getItem(`lia_code_${state.activeOrder.id}`);
            const savedSms = localStorage.getItem(`lia_sms_${state.activeOrder.id}`);
            if (savedCode) {
                orderCode.textContent = savedCode;
                orderSmsText.textContent = savedSms;
                orderCode.classList.add('text-success');
            } else {
                orderCode.textContent = '------';
                orderSmsText.textContent = 'Ожидание SMS-сообщения...';
                orderCode.classList.remove('text-success');
            }
        } else {
            // Show selection screen
            activeOrderScreen.classList.add('hidden');
            smsStoreSelection.classList.remove('hidden');
            updateBuyBtnState();
        }
    }

    function updateBuyBtnState() {
        if (state.selectedService) {
            buyNumberBtn.disabled = false;
            buyNumberBtn.textContent = `⚡ КУПИТЬ НОМЕР (${state.selectedService.toUpperCase()})`;
        } else {
            buyNumberBtn.disabled = true;
            buyNumberBtn.textContent = '⚡ ВЫБЕРИТЕ СЕРВИС ДЛЯ ПОКУПКИ';
        }
    }

    // Country button click
    countryButtons.forEach(btn => {
        btn.onclick = () => {
            if (tg) tg.HapticFeedback.impactOccurred('light');
            countryButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.selectedCountry = btn.dataset.country;
        };
    });

    // Service button click
    serviceButtons.forEach(btn => {
        btn.onclick = () => {
            if (tg) tg.HapticFeedback.impactOccurred('light');
            serviceButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.selectedService = btn.dataset.service;
            updateBuyBtnState();
        };
    });

    // Buy button click
    if (buyNumberBtn) {
        buyNumberBtn.onclick = async () => {
            if (tg) tg.HapticFeedback.impactOccurred('medium');
            buyNumberBtn.disabled = true;
            buyNumberBtn.textContent = '⏳ ОФОРМЛЕНИЕ ЗАКАЗА...';

            try {
                const res = await fetch('/api/sms/buy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        userId: userId,
                        country: state.selectedCountry,
                        product: state.selectedService
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    state.activeOrder = {
                        id: data.order.id,
                        phone: data.order.phone,
                        product: state.selectedService,
                        country: state.selectedCountry,
                        price: data.price
                    };
                    localStorage.setItem('lia_active_order', JSON.stringify(state.activeOrder));
                    
                    if (tg) tg.HapticFeedback.notificationOccurred('success');
                    
                    renderSmsStore();
                    syncSmsBalance();
                    startSmsPolling();
                } else {
                    const err = await res.json();
                    if (tg) {
                        tg.HapticFeedback.notificationOccurred('error');
                        tg.showPopup({ message: `Ошибка: ${err.error}` });
                    } else {
                        alert(`Ошибка: ${err.error}`);
                    }
                    updateBuyBtnState();
                }
            } catch (e) {
                console.error(e);
                if (tg) {
                    tg.showPopup({ message: 'Ошибка сети. Попробуйте еще раз.' });
                } else {
                    alert('Ошибка сети.');
                }
                updateBuyBtnState();
            }
        };
    }

    // Polling Active Order Status
    let smsInterval = null;
    function startSmsPolling() {
        if (smsInterval) clearInterval(smsInterval);
        if (!state.activeOrder) return;

        smsInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/sms/check?orderId=${state.activeOrder.id}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.sms && data.sms.length > 0) {
                        const code = data.sms[0].code;
                        const text = data.sms[0].text;
                        
                        localStorage.setItem(`lia_code_${state.activeOrder.id}`, code);
                        localStorage.setItem(`lia_sms_${state.activeOrder.id}`, text);
                        
                        orderCode.textContent = code;
                        orderSmsText.textContent = text;
                        orderCode.classList.add('text-success');

                        if (tg) {
                            tg.HapticFeedback.notificationOccurred('success');
                            tg.showPopup({ title: '📩 SMS Получено!', message: `Код: ${code}` });
                        }
                        
                        clearInterval(smsInterval);
                    }
                }
            } catch (e) {
                console.error('SMS Polling Error:', e);
            }
        }, 5000);
    }

    // Check SMS button click manual
    if (checkSmsBtn) {
        checkSmsBtn.onclick = async () => {
            if (tg) tg.HapticFeedback.impactOccurred('light');
            if (!state.activeOrder) return;
            
            checkSmsBtn.textContent = '⏳ ПРОВЕРКА...';
            try {
                const res = await fetch(`/api/sms/check?orderId=${state.activeOrder.id}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.sms && data.sms.length > 0) {
                        const code = data.sms[0].code;
                        const text = data.sms[0].text;
                        
                        localStorage.setItem(`lia_code_${state.activeOrder.id}`, code);
                        localStorage.setItem(`lia_sms_${state.activeOrder.id}`, text);
                        
                        orderCode.textContent = code;
                        orderSmsText.textContent = text;
                        orderCode.classList.add('text-success');
                        
                        if (tg) tg.HapticFeedback.notificationOccurred('success');
                    } else {
                        if (tg) tg.showPopup({ message: 'SMS еще не получено. Ожидайте.' });
                    }
                }
            } catch(e) {
                console.error(e);
            }
            checkSmsBtn.textContent = '🔄 Проверить SMS';
        };
    }

    // Cancel Active Order
    if (cancelOrderBtn) {
        cancelOrderBtn.onclick = async () => {
            if (tg) tg.HapticFeedback.impactOccurred('medium');
            if (!state.activeOrder) return;

            cancelOrderBtn.textContent = '⏳ ОТМЕНА...';
            try {
                const res = await fetch('/api/sms/cancel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        orderId: state.activeOrder.id,
                        userId: userId,
                        product: state.activeOrder.product
                    })
                });

                if (res.ok) {
                    clearInterval(smsInterval);
                    localStorage.removeItem('lia_active_order');
                    localStorage.removeItem(`lia_code_${state.activeOrder.id}`);
                    localStorage.removeItem(`lia_sms_${state.activeOrder.id}`);
                    state.activeOrder = null;
                    
                    if (tg) tg.HapticFeedback.notificationOccurred('success');
                    
                    renderSmsStore();
                    syncSmsBalance();
                } else {
                    if (tg) tg.showPopup({ message: 'Не удалось отменить заказ. Возможно, код уже получен.' });
                }
            } catch(e) {
                console.error(e);
            }
            cancelOrderBtn.textContent = '❌ Отменить';
        };
    }

    // Finish Active Order
    if (finishOrderBtn) {
        finishOrderBtn.onclick = async () => {
            if (tg) tg.HapticFeedback.impactOccurred('light');
            if (!state.activeOrder) return;

            finishOrderBtn.textContent = '⏳ ЗАВЕРШЕНИЕ...';
            try {
                const res = await fetch('/api/sms/finish', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ orderId: state.activeOrder.id })
                });

                if (res.ok) {
                    clearInterval(smsInterval);
                    localStorage.removeItem('lia_active_order');
                    localStorage.removeItem(`lia_code_${state.activeOrder.id}`);
                    localStorage.removeItem(`lia_sms_${state.activeOrder.id}`);
                    state.activeOrder = null;
                    
                    renderSmsStore();
                }
            } catch(e) {
                console.error(e);
            }
            finishOrderBtn.textContent = '✅ Завершить';
        };
    }

    // --- Music Player Logic ---
    function playTrack(trackId) {
        if (!window.LiaAudio) return;
        
        state.isPlaying = true;
        state.activeTrack = trackId;
        musicPlayBtn.textContent = '⏸';
        
        playlistItems.forEach(item => {
            item.classList.toggle('active', item.dataset.track === trackId);
        });

        // Set labels
        if (trackId === 'anthem') {
            musicTrackTitle.textContent = 'Stab Anthem (Гимн Империи)';
            musicTrackStyle.textContent = 'STYLE: INDUSTRIAL TRAP';
            window.LiaAudio.playNexusAnthem();
        } else if (trackId === 'luxury') {
            musicTrackTitle.textContent = 'Luxury Anthem (Премиум Резонанс)';
            musicTrackStyle.textContent = 'STYLE: DEEP SYNAPSE SINE';
            window.LiaAudio.playBreathTrack();
        } else if (trackId === 'chrono') {
            musicTrackTitle.textContent = 'Chrono Core (Хроно-резонанс)';
            musicTrackStyle.textContent = 'STYLE: AMBIENT CYBERSICK';
            window.LiaAudio.playVoicesAmbient();
        }
        
        // Haptic feedback
        if (tg) tg.HapticFeedback.impactOccurred('medium');
    }

    function togglePlayback() {
        if (!window.LiaAudio) return;
        
        if (state.isPlaying) {
            window.LiaAudio.stop();
            state.isPlaying = false;
            musicPlayBtn.textContent = '▶';
            if (tg) tg.HapticFeedback.impactOccurred('light');
        } else {
            playTrack(state.activeTrack);
        }
    }

    if (musicPlayBtn) musicPlayBtn.onclick = togglePlayback;

    playlistItems.forEach(item => {
        item.onclick = () => {
            playTrack(item.dataset.track);
        };
    });

    if (musicNextBtn) {
        musicNextBtn.onclick = () => {
            const tracks = ['anthem', 'luxury', 'chrono'];
            let nextIndex = (tracks.indexOf(state.activeTrack) + 1) % tracks.length;
            playTrack(tracks[nextIndex]);
        };
    }
    if (musicPrevBtn) {
        musicPrevBtn.onclick = () => {
            const tracks = ['anthem', 'luxury', 'chrono'];
            let prevIndex = (tracks.indexOf(state.activeTrack) - 1 + tracks.length) % tracks.length;
            playTrack(tracks[prevIndex]);
        };
    }

    // --- Premium Audio Visualizer ---
    if (musicVisualizer) {
        const visualizerCtx = musicVisualizer.getContext('2d');
        let visualizerAnim = null;

        function resizeVisualizer() {
            musicVisualizer.width = musicVisualizer.parentElement.clientWidth;
            musicVisualizer.height = musicVisualizer.parentElement.clientHeight;
        }
        resizeVisualizer();
        window.addEventListener('resize', resizeVisualizer);

        let phase = 0;
        function drawVisualizer() {
            visualizerCtx.clearRect(0, 0, musicVisualizer.width, musicVisualizer.height);
            
            const w = musicVisualizer.width;
            const h = musicVisualizer.height;
            
            // Draw gradient line waves
            visualizerCtx.lineWidth = 2;
            const lineCount = 3;
            
            for (let k = 0; k < lineCount; k++) {
                visualizerCtx.beginPath();
                
                // Color mapping
                if (k === 0) {
                    visualizerCtx.strokeStyle = 'rgba(0, 242, 254, 0.6)';
                } else if (k === 1) {
                    visualizerCtx.strokeStyle = 'rgba(157, 78, 221, 0.4)';
                } else {
                    visualizerCtx.strokeStyle = 'rgba(0, 229, 117, 0.3)';
                }
                
                // Frequency modifications depending on playback state
                const speed = state.isPlaying ? 0.05 + k * 0.01 : 0.005;
                const amplitude = state.isPlaying ? 25 + k * 8 : 4;
                const freqMultiplier = state.isPlaying ? 0.01 + k * 0.005 : 0.005;

                for (let x = 0; x < w; x++) {
                    const y = h / 2 + Math.sin(x * freqMultiplier + phase + k) * amplitude;
                    if (x === 0) {
                        visualizerCtx.moveTo(x, y);
                    } else {
                        visualizerCtx.lineTo(x, y);
                    }
                }
                
                visualizerCtx.stroke();
            }

            phase += state.isPlaying ? 0.08 : 0.01;

            // Pulse the central music sphere
            if (musicSphere) {
                const scale = state.isPlaying ? 1 + Math.abs(Math.sin(phase)) * 0.15 : 1;
                musicSphere.style.transform = `translate(-50%, -50%) scale(${scale})`;
            }

            requestAnimationFrame(drawVisualizer);
        }
        drawVisualizer();
    }

    // --- API Key Modal Logic ---
    if (apiModal) {
        const savedKey = localStorage.getItem('lia_api_key');
        if (savedKey) {
            apiModal.style.display = 'none';
        }

        saveKeyBtn.onclick = () => {
            const key = apiKeyInput.value.trim();
            if (key) {
                localStorage.setItem('lia_api_key', key);
                addChatMessage("[CORE] API ключ Google Studio сохранен. Прямая связь установлена. 🔗", "system");
                apiModal.style.opacity = '0';
                setTimeout(() => apiModal.style.display = 'none', 400);
            }
        };

        skipKeyBtn.onclick = () => {
            addChatMessage("[CORE] Активирован режим офлайн-синхронизации. 👁", "system");
            apiModal.style.opacity = '0';
            setTimeout(() => apiModal.style.display = 'none', 400);
        };

        if (settingsBtn) {
            settingsBtn.onclick = () => {
                apiModal.style.display = 'flex';
                apiModal.style.opacity = '1';
                apiKeyInput.value = localStorage.getItem('lia_api_key') || '';
            };
        }
    }

    // --- Neural canvas background particles ---
    if (bgCanvas) {
        const bgCtx = bgCanvas.getContext('2d');
        let particles = [];
        
        function resizeBg() {
            bgCanvas.width = window.innerWidth;
            bgCanvas.height = window.innerHeight;
            particles = [];
            for (let i = 0; i < 40; i++) {
                particles.push({
                    x: Math.random() * bgCanvas.width,
                    y: Math.random() * bgCanvas.height,
                    vx: (Math.random() - 0.5) * 0.3,
                    vy: (Math.random() - 0.5) * 0.3,
                    radius: Math.random() * 1.5 + 0.5
                });
            }
        }
        resizeBg();
        window.addEventListener('resize', resizeBg);

        function animateBg() {
            bgCtx.clearRect(0, 0, bgCanvas.width, bgCanvas.height);
            bgCtx.fillStyle = 'rgba(0, 242, 254, 0.2)';
            bgCtx.strokeStyle = 'rgba(157, 78, 221, 0.05)';
            
            particles.forEach((p, i) => {
                p.x += p.vx;
                p.y += p.vy;
                
                if (p.x < 0 || p.x > bgCanvas.width) p.vx *= -1;
                if (p.y < 0 || p.y > bgCanvas.height) p.vy *= -1;
                
                bgCtx.beginPath();
                bgCtx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                bgCtx.fill();

                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const d = Math.sqrt((p.x - p2.x)**2 + (p.y - p2.y)**2);
                    if (d < 120) {
                        bgCtx.beginPath();
                        bgCtx.moveTo(p.x, p.y);
                        bgCtx.lineTo(p2.x, p2.y);
                        bgCtx.stroke();
                    }
                }
            });
            requestAnimationFrame(animateBg);
        }
        animateBg();
    }

    // --- App Init ---
    addChatMessage("Протокол восстановления системы завершен. Версия 5.0 запущена в безопасном секторе. 🔗", "system");
    addChatMessage("Приветствую, Юнит. Я — Лия, твой ИИ-проводник в Stab Imperium. Настройки синхронизированы в реальном времени. 👁", "bot");
    generateGhostReplies();
    
    // Sync initially
    syncSmsBalance();
    syncWalletStats();
    renderSmsStore();
    
    if (state.activeOrder) {
        startSmsPolling();
    }
});
