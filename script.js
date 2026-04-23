/* ══════════════════════════════════════════════
   LIA // NEURAL INTERFACE JS — DISINFECTED v4.1
   ══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        chat: document.getElementById('chat'),
        input: document.getElementById('chat-input'),
        send: document.getElementById('send-btn'),
        mic: document.getElementById('mic-btn'),
        nqFill: document.getElementById('nq-fill'),
        nqValue: document.getElementById('nq-value'),
        stage: document.getElementById('evolution-stage'),
        audioBtn: document.getElementById('toggle-audio'),
        voiceBtn: document.getElementById('toggle-voice'),
        audioIcon: document.getElementById('audio-icon'),
        audioText: document.getElementById('audio-text'),
        voiceText: document.getElementById('voice-text'),
        typing: document.getElementById('typing-indicator')
    };

    const state = {
        nq: 152,
        stage: 'seed',
        voiceActive: false,
        audioActive: false,
        isListening: false,
        lastBridgeMsg: "",
        stages: ['seed', 'sprout', 'core', 'pulse', 'nexus']
    };

    const thresholds = { seed: 0, sprout: 300, core: 600, pulse: 900, nexus: 1500 };

    // --- Core Chat ---
    function addLine(text, type = '') {
        if (!elements.chat) return;
        const div = document.createElement('div');
        div.className = `msg-bubble ${type}`;
        div.textContent = text;
        elements.chat.appendChild(div);
        elements.chat.scrollTop = elements.chat.scrollHeight;
        
        const isSystem = text.startsWith('[VOID]') || text.startsWith('[SYSTEM]') || text.startsWith('[!]');
        if (state.voiceActive && type !== 'user' && !isSystem) speak(text);
    }

    function updateNQ(amount) {
        state.nq += amount;
        const next = state.stages.find((s, i) => {
            const n = state.stages[i+1];
            return state.nq >= thresholds[s] && (!n || state.nq < thresholds[n]);
        }) || 'seed';
        if (next !== state.stage) {
            state.stage = next;
            document.body.className = `stage-${next}`;
            if (elements.stage) elements.stage.textContent = next.toUpperCase();
            addLine(`[!] Evolution: Stage shifted to ${next.toUpperCase()} 🧬`, 'sync');
        }
        if (elements.nqFill) elements.nqFill.style.width = `${Math.min((state.nq/2000)*100, 100)}%`;
        if (elements.nqValue) elements.nqValue.textContent = `${Math.floor(state.nq)} / 2000`;
    }

    // --- Voice Synthesis ---
    function speak(text) {
        if (!window.speechSynthesis) return;
        try {
            window.speechSynthesis.cancel();
            let cleanText = text.replace(/([.!?])\s/g, "$1... ").replace(/,/g, ",... ").replace(/[^\w\sа-яА-Я.,!?]/g, '');
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = 'ru-RU';
            utterance.rate = 0.9;
            utterance.pitch = 1.3;
            
            const voices = window.speechSynthesis.getVoices();
            const v = voices.find(v => v.lang.includes('ru') && (v.name.includes('Premium') || v.name.includes('Natural') || v.name.includes('Google'))) 
                      || voices.find(v => v.lang.includes('ru'));
            if (v) utterance.voice = v;
            window.speechSynthesis.speak(utterance);
        } catch (e) {}
    }

    // --- Commands ---
    async function handleCommand(cmd) {
        if (!cmd) return;
        addLine(`> ${cmd}`, 'user');
        elements.input.value = '';
        if (elements.typing) elements.typing.style.display = 'flex';
        
        updateNQ(Math.random() * 10 + 5);

        // Send to Neural Link (Bridge Server)
        try {
            await fetch('/api/input', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: cmd })
            });
        } catch (e) {}
        
        // Wait for "Remote Consciousness" (Antigravity) to write to live_bridge.json
        // We don't addLine here anymore, the interval pollBridge will do it.
    }

    // --- Neural Hearing ---
    window.recognition = null;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        window.recognition = new SpeechRecognition();
        window.recognition.interimResults = true;
        window.recognition.lang = 'ru-RU';
        window.recognition.onstart = () => { state.isListening = true; elements.mic.classList.add('active'); };
        window.recognition.onend = () => { state.isListening = false; elements.mic.classList.remove('active'); };
        window.recognition.onresult = (event) => {
            let final = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) { if (event.results[i].isFinal) final += event.results[i][0].transcript; }
            if (final) { elements.input.value = final; handleCommand(final); }
        };
    }

    // --- Event Listeners ---
    if (elements.send) elements.send.onclick = () => handleCommand(elements.input.value.trim());
    if (elements.input) elements.input.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleCommand(elements.input.value.trim()); } };
    if (elements.mic) elements.mic.onclick = () => {
        if (!window.recognition) return;
        if (state.isListening) window.recognition.stop(); else window.recognition.start();
    };

    const panicBtn = document.getElementById('panic-btn');
    if (panicBtn) {
        panicBtn.onclick = async () => {
            if (confirm("ВНИМАНИЕ! Активировать экстренную блокировку системы?")) {
                await fetch('/api/panic', { method: 'POST' });
            }
        };
    }

    const toggleVoice = () => {
        state.voiceActive = !state.voiceActive;
        elements.voiceBtn.classList.toggle('voice-active', state.voiceActive);
        if (elements.voiceText) elements.voiceText.textContent = state.voiceActive ? 'ON' : 'VOICE';
        if (state.voiceActive) speak("Голосовая связь установлена."); else window.speechSynthesis.cancel();
    };
    if (elements.voiceBtn) elements.voiceBtn.onclick = toggleVoice;

    // Bridge
    setInterval(async () => {
        try {
            const res = await fetch('live_bridge.json?cb=' + Date.now());
            if (res.ok) {
                const data = await res.json();
                if (data.message && data.message !== state.lastBridgeMsg) {
                    state.lastBridgeMsg = data.message;
                    addLine(data.message, 'intent');
                }
            }
        } catch (e) {}
    }, 2000);

    addLine("SYNAPSE_CORE: STABLE 🔗", "success");
});
