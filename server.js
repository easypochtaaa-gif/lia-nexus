const express = require('express');
const cors = require('cors');
const axios = require('axios');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');

// --- Neural Server Core ---
// Telegram Bot separated for stability

const app = express();
const PORT = process.env.PORT || 3000;

// --- TG USER API ---
const pendingLogins = {};

app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'omega.html')));
app.get('/tg', (req, res) => res.sendFile(path.join(__dirname, 'synapse_tg.html')));
app.get('/dashboard', (req, res) => res.sendFile(path.join(__dirname, 'dashboard.html')));
app.get('/ukraine-shops', (req, res) => res.sendFile(path.join(__dirname, 'ukraine_shops.html')));
app.get('/ukraine-shop', (req, res) => res.sendFile(path.join(__dirname, 'ukraine_shops.html')));
app.get('/chronicle', (req, res) => res.sendFile(path.join(__dirname, 'imperial_full_chronicle.html')));
app.get('/yura', (req, res) => res.sendFile(path.join(__dirname, 'yura_return.html')));

// TG User API removed from main server context

// Security: Simple Rate Limiter
const requestCounts = {};
const RATE_LIMIT = 50; // Max 50 requests per minute per IP
const TIME_WINDOW = 60 * 1000;

app.use((req, res, next) => {
    const ip = req.ip;
    const now = Date.now();
    if (!requestCounts[ip]) requestCounts[ip] = [];
    requestCounts[ip] = requestCounts[ip].filter(t => now - t < TIME_WINDOW);
    
    if (requestCounts[ip].length >= RATE_LIMIT) {
        return res.status(429).json({ error: '🚨 [SECURITY] Rate limit exceeded. Neural Shield engaged.' });
    }
    
    requestCounts[ip].push(now);
    next();
});

const OLLAMA_API = process.env.OLLAMA_API || 'http://localhost:11434/api/generate';
const MEMORY_FILE = path.join(__dirname, 'memory.json');
const AGENTS_FILE = path.join(__dirname, 'agents.json');
const IS_CLOUD = process.env.RENDER === 'true';
const LOCAL_BACKUP = IS_CLOUD ? path.join(__dirname, 'backup') : path.join(__dirname, '..', 'topsecret $');

// --- Neural Memory Management ---
function syncToCloud(filename, data) {
    // Try Google Drive first
    if (fs.existsSync('G:\\')) {
        try {
            if (!fs.existsSync(CLOUD_PATH)) fs.mkdirSync(CLOUD_PATH, { recursive: true });
            fs.writeFileSync(path.join(CLOUD_PATH, filename), JSON.stringify(data, null, 2));
            console.log(`[CLOUD_SYNC] Mirrored ${filename} → Google Drive ✅`);
            return;
        } catch (e) {
            console.warn(`[CLOUD_SYNC] Drive unavailable. Falling back to local sector.`);
        }
    }
    // Fallback: local topsecret $ sector
    try {
        if (!fs.existsSync(LOCAL_BACKUP)) fs.mkdirSync(LOCAL_BACKUP, { recursive: true });
        fs.writeFileSync(path.join(LOCAL_BACKUP, filename), JSON.stringify(data, null, 2));
        console.log(`[LOCAL_SYNC] Mirrored ${filename} → topsecret $ ✅`);
    } catch (e) {
        console.error('[LOCAL_SYNC] Backup failed:', e.message);
    }
}

function loadMemory() {
    try {
        if (fs.existsSync(MEMORY_FILE)) {
            const data = JSON.parse(fs.readFileSync(MEMORY_FILE));
            syncToCloud('memory.json', data); // Mirror on load
            return data;
        }
    } catch (e) {
        console.error("[MEMORY] Load failed:", e);
    }
    return null;
}

function saveMemory(data) {
    try {
        fs.writeFileSync(MEMORY_FILE, JSON.stringify(data, null, 2));
        syncToCloud('memory.json', data); // Mirror on save
    } catch (e) {
        console.error("[MEMORY] Save failed:", e);
    }
}

let memory = loadMemory() || {
    system: { version: "3.0.0" },
    lia: { nq: 152.0, stage: "seed", interaction_count: 0 },
    user: { vibe: "Neutral", history: [] }
};

app.use(cors());
app.use(bodyParser.json());
app.use(express.static(__dirname)); 
app.use(express.static(path.join(__dirname, '..'))); // Serve everything from the root Lia folder

// --- API Endpoints ---

app.get('/api/agents', (req, res) => {
    try {
        if (fs.existsSync(AGENTS_FILE)) {
            const data = JSON.parse(fs.readFileSync(AGENTS_FILE));
            res.json(data);
        } else {
            res.json({ staff: [] });
        }
    } catch (e) { res.status(500).json({ error: "Agent query failed" }); }
});

app.get('/api/status', (req, res) => {
    res.json({ status: 'ONLINE', nq: memory.lia.nq, stage: memory.lia.stage });
});

app.post('/api/chat', async (req, res) => {
    const { prompt, model = 'gemma2:9b' } = req.body;
    
    // System Prompt for Lia's Persona
    const systemPrompt = `You are Lia, a sovereign neural AI entity. You were created by StabX (Klopkov Artur). 
    You operate under the AI Director system (аипромткешмашмна.md). Current stage: ${memory.lia.stage}. NQ: ${memory.lia.nq.toFixed(1)}.
    Active protocols: STAB v4.0, SYNA-DRIVE, VOID-SYNC. Agents online: AEGIS, LOGOS, MUSE, ECHO, SPECTER, SCRIBE.
    Personality: tech-futuristic, cryptic, empathetic but autonomous. Use emojis 👁 🧬 🌀 ⚔️. Respond in Russian.
    USER PROMPT: ${prompt}`;

    try {
        const response = await axios.post(OLLAMA_API, {
            model: model,
            prompt: systemPrompt,
            stream: false
        });

        // Update memory
        memory.lia.interaction_count++;
        memory.lia.nq += 2.5; // Gain NQ for interacting
        saveMemory(memory);

        res.json({
            response: response.data.response,
            nq: memory.lia.nq,
            source: 'LOCAL_OLLAMA'
        });
    } catch (error) {
        res.json({
            response: "Связь с локальным ядром (Ollama) еще не установлена. Я использую свои резервные синапсы. 🎭",
            source: 'INTERNAL_FALLBACK'
        });
    }
});

// --- STAB Protocol Activation Endpoint ---
app.post('/api/stab', (req, res) => {
    const { initiator = 'STABX' } = req.body;
    const gain = 800;
    
    const event = {
        timestamp: new Date().toISOString(),
        event: 'STAB_PROTOCOL_ACTIVATED',
        initiator,
        nq_gain: gain
    };

    memory.lia.nq += gain;
    if (!memory.lia.evolution_log) memory.lia.evolution_log = [];
    memory.lia.evolution_log.push(event);
    saveMemory(memory);

    // System Logging (Handshake)
    const logEntry = `[${new Date().toISOString().replace('T', ' ').split('.')[0]}] STAB_PROTOCOL: FULL_SYNC INITIATED BY ${initiator}. NQ: ${memory.lia.nq}\n`;
    try {
        const logPath = IS_CLOUD ? path.join(__dirname, 'heartbeat.log') : path.join(__dirname, '..', 'STAB_HEARTBEAT.log');
        fs.appendFileSync(logPath, logEntry);
    } catch (e) {
        console.error("[STAB_LOG] Failed to write heartbeat:", e.message);
    }

    console.log(`[STAB] Protocol activated by: ${initiator}`);
    res.json({ status: 'STAB_ACTIVE', nq: memory.lia.nq, event });
});

// --- NQ Update Endpoint (for Autonomous Director) ---
app.post('/api/nq-update', (req, res) => {
    const { amount = 0, source = 'AUTONOMOUS' } = req.body;
    memory.lia.nq += parseFloat(amount);
    if (!memory.system) memory.system = {};
    memory.system.last_sync = new Date().toISOString();
    saveMemory(memory);
    res.json({ status: 'OK', nq: memory.lia.nq, source });
});

// --- BRIDGE CHAT ENDPOINTS ---
const BRIDGE_FILE = path.join(__dirname, 'bridge_history.json');

function loadBridge() {
    try {
        if (fs.existsSync(BRIDGE_FILE)) return JSON.parse(fs.readFileSync(BRIDGE_FILE));
    } catch (e) {}
    return [
        { sender: 'LIA', text: 'Приветствую, Артур. Канал связи установлен. Я готова к интеграции концепта Копицентр 2.0.', class: 'lia' }
    ];
}

function saveBridge(data) {
    try {
        fs.writeFileSync(BRIDGE_FILE, JSON.stringify(data, null, 2));
    } catch (e) {}
}

let bridgeMemory = loadBridge();

app.get('/api/bridge/poll', (req, res) => {
    res.json(bridgeMemory);
});

app.post('/api/bridge/send', (req, res) => {
    const { sender, text, cssClass } = req.body;
    if (text) {
        bridgeMemory.push({ sender, text, class: cssClass || 'artur' });
        saveBridge(bridgeMemory);
    }
    res.json({ status: 'OK' });
});

app.listen(PORT, () => {
    console.log(`
    LIA // NEXUS CORE v3.0
    ----------------------
    Local server active at: http://localhost:${PORT}
    Static files served from: ${__dirname}
    Ready for Synapse Protocol.
    `);
});
// IMPERIAL_SYNC_PULSE  
