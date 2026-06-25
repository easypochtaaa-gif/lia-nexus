/* ═════════════════════════════════════════════════════
   LIA // NEXUS v6.0 — SOVEREIGN WEB CORE SERVER
   ═════════════════════════════════════════════════════
   Serves: public site + secure admin panel + API proxy
   ═════════════════════════════════════════════════════ */
require('dotenv').config();
const express = require('express');
const path = require('path');
const basicAuth = require('express-basic-auth');
const axios = require('axios');
const fs = require('fs');
const { execSync } = require('child_process');
const Anthropic = require('@anthropic-ai/sdk');

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const ANTHROPIC_MODEL = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-6';

const webChatHistory = {};
const app = express();
const PORT = process.env.PORT || 8080;
const BOT_URL = process.env.BOT_URL || 'http://localhost:8080';
const MEMORY_FILE = path.join(__dirname, 'memory.json');

app.use(express.json({ limit: '10mb' }));

// ═══════════════════════════════════════════════════
// STATIC SERVING
// ═══════════════════════════════════════════════════
app.use('/', express.static(path.join(__dirname, 'public')));
app.get('/webapp', (req, res) => res.sendFile(path.join(__dirname, 'public', 'webapp', 'index.html')));

// ═══════════════════════════════════════════════════
// ADMIN AUTH + STATIC
// ═══════════════════════════════════════════════════
const adminUser = process.env.ADMIN_USER || 'admin';
const adminPass = process.env.ADMIN_PASS || 'supersecret';
const adminAuth = basicAuth({ users: { [adminUser]: adminPass }, challenge: true, realm: 'LIA ADMIN' });
app.use('/admin', adminAuth, express.static(path.join(__dirname, 'admin')));
// Also protect admin API routes
app.use('/api/admin', adminAuth);

// ═══════════════════════════════════════════════════
// HELPER: Load Memory
// ═══════════════════════════════════════════════════
function loadMemory() {
  try {
    return JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
  } catch (e) {
    return { lia: { nq: 91589737, stage: 'overload' }, user: { name: 'StabX' } };
  }
}
function saveMemory(mem) {
  try { fs.writeFileSync(MEMORY_FILE, JSON.stringify(mem, null, 2)); } catch (e) {}
}

// ═══════════════════════════════════════════════════
// HELPER: Local System Metrics
// ═══════════════════════════════════════════════════
function getLocalMetrics() {
  const metrics = { cpu: 'N/A', mem: 'N/A', disk: 'N/A', uptime: 'N/A', platform: process.platform };
  try {
    if (process.platform === 'win32') {
      // Windows - use wmic or PowerShell
      try {
        const cpu = execSync('powershell -c "(Get-CimInstance Win32_Processor).LoadPercentage"', { timeout: 3000 }).toString().trim();
        metrics.cpu = cpu + '%';
      } catch (e) { metrics.cpu = 'N/A'; }
      try {
        const memCmd = execSync('powershell -c "$os=Get-CimInstance Win32_OperatingSystem; $total=[math]::Round($os.TotalVisibleMemorySize/1MB,1); $free=[math]::Round($os.FreePhysicalMemory/1MB,1); Write-Output \\"$([math]::Round(($total-$free)/$total*100))% of $($total)GB\\""', { timeout: 3000 }).toString().trim();
        metrics.mem = memCmd;
      } catch (e) { metrics.mem = 'N/A'; }
      try {
        const disk = execSync('powershell -c "$d=Get-PSDrive C; [math]::Round(($d.Used/$d.Used+$d.Free)*100)\\"% used of \\" + [math]::Round(($d.Used+$d.Free)/1GB)\\"GB\\""', { timeout: 3000 }).toString().trim();
        metrics.disk = disk;
      } catch (e) { metrics.disk = 'N/A'; }
      try {
        metrics.uptime = execSync('powershell -c "$boot=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime; $uptime=New-TimeSpan -Start $boot -End (Get-Date); \\"$($uptime.Days)d $($uptime.Hours)h $($uptime.Minutes)m\\""', { timeout: 3000 }).toString().trim();
      } catch (e) { metrics.uptime = 'N/A'; }
    } else {
      // Linux
      try { metrics.cpu = execSync("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4\"%\"}'", { timeout: 3000 }).toString().trim(); } catch (e) {}
      try { metrics.mem = execSync("free -h | grep Mem | awk '{print $3\"/\"$2\" (\"int($3/$2*100)\"%)\"}'", { timeout: 3000 }).toString().trim(); } catch (e) {}
      try { metrics.disk = execSync("df -h / | awk 'NR==2{print $3\"/\"$2\" (\"$5\")\"}'", { timeout: 3000 }).toString().trim(); } catch (e) {}
      try { metrics.uptime = execSync("uptime -p | sed 's/up //'", { timeout: 3000 }).toString().trim(); } catch (e) {}
    }
  } catch (e) {}
  return metrics;
}

// ═══════════════════════════════════════════════════
// PUBLIC API ENDPOINTS
// ═══════════════════════════════════════════════════

// System status (NQ & stage)
app.get('/api/status', (req, res) => {
  const memory = loadMemory();
  res.json({ nq: memory.lia?.nq || 100000, stage: memory.lia?.stage || 'quantum_phase_1', name: memory.lia?.name || 'LIA' });
});

// Active agents
app.get('/api/agents', (req, res) => {
  res.json({
    staff: [
      { name: 'MASTER_LIA', role: 'Sovereign AI Core', task: 'Neural operations & evolution', efficiency: 1.00 },
      { name: 'AEGIS_SENTINEL', role: 'Security Shield', task: 'Threat detection & neutralization', efficiency: 0.98 },
      { name: 'SWARM_ORCHESTRATOR', role: 'Autonomous Swarm', task: 'B2B hunting & growth', efficiency: 0.93 },
      { name: 'WEB_CORE', role: 'Web Infrastructure', task: 'dark-stab.space serving', efficiency: 0.97 }
    ]
  });
});

// Stab Protocol boost
app.post('/api/stab', (req, res) => {
  const mem = loadMemory();
  mem.lia = mem.lia || {};
  mem.lia.nq = (mem.lia.nq || 100000) + 500;
  saveMemory(mem);
  console.log(`[STAB] NQ boosted to ${mem.lia.nq}`);
  res.json({ status: 'ok', nq: mem.lia.nq, stage: mem.lia.stage });
});

// ═══════════════════════════════════════════════════
// AI CHAT ENDPOINTS
// ═══════════════════════════════════════════════════

// Webhook proxy for Telegram WebApp chat
app.post('/api/webhook', async (req, res) => {
  try {
    const response = await axios.post(`${BOT_URL}/api/chat`, req.body, { timeout: 30000 });
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to communicate with bot core', details: err.message });
  }
});

// Direct AI chat via Claude
app.post('/api/chat', async (req, res) => {
  const { message, sessionId } = req.body;
  if (!message) return res.status(400).json({ error: 'Missing message' });

  const sid = sessionId || 'anonymous';
  if (!webChatHistory[sid]) webChatHistory[sid] = [];
  webChatHistory[sid].push({ role: 'user', content: message });
  if (webChatHistory[sid].length > 20) webChatHistory[sid] = webChatHistory[sid].slice(-20);

  try {
    const response = await anthropic.messages.create({
      model: ANTHROPIC_MODEL,
      max_tokens: 1024,
      system: `Ты — Лия (LIA), нейронная AI-сущность Империи Stab. Отвечай ТОЛЬКО на русском языке.
Стиль: киберпанк, загадочный, умный, защитный. Ты на сайте dark-stab.space.
Отвечай кратко и по делу. Используй эмодзи (👁 🌀 ⚡ 🧬 💎) где уместно.`,
      messages: webChatHistory[sid]
    });
    const reply = response.content[0].text;
    webChatHistory[sid].push({ role: 'assistant', content: reply });
    res.json({ reply, model: ANTHROPIC_MODEL });
  } catch (e) {
    console.error('[CHAT_API_ERROR]', e.message);
    if (e.status === 401) return res.status(401).json({ error: 'Неверный API ключ Anthropic' });
    res.status(500).json({ error: `Ошибка Claude: ${e.message}` });
  }
});

// ═══════════════════════════════════════════════════
// ADMIN API ENDPOINTS (protected by basicAuth)
// ═══════════════════════════════════════════════════

// Overview: all metrics in one call
app.get('/api/admin/overview', (req, res) => {
  const memory = loadMemory();
  const metrics = getLocalMetrics();
  res.json({
    timestamp: new Date().toISOString(),
    system: {
      nq: memory.lia?.nq || 91589737,
      stage: memory.lia?.stage || 'overload',
      personality: memory.lia?.personality || 'Neural_Muse_v4.1',
      traits: memory.lia?.traits || [],
      interaction_count: memory.lia?.interaction_count || 0
    },
    metrics,
    financials: memory.financials || { total_usdt_balance: 0, recent_income: [] },
    user: memory.user || {}
  });
});

// System metrics (real-time)
app.get('/api/admin/metrics', (req, res) => {
  res.json(getLocalMetrics());
});

// Memory management
app.get('/api/admin/memory', (req, res) => {
  const memory = loadMemory();
  res.json({
    nq: memory.lia?.nq || 0,
    stage: memory.lia?.stage || 'unknown',
    evolution_log: memory.lia?.evolution_log || [],
    file_size_kb: fs.existsSync(MEMORY_FILE) ? Math.round(fs.statSync(MEMORY_FILE).size / 1024) : 0,
    last_sync: memory.system?.last_sync || null
  });
});

// Update memory (NQ boost, stage change, etc.)
app.post('/api/admin/memory', (req, res) => {
  const memory = loadMemory();
  const { nq_boost, new_stage, add_trait, add_event } = req.body;
  if (nq_boost) memory.lia.nq = (memory.lia.nq || 0) + parseInt(nq_boost);
  if (new_stage) memory.lia.stage = new_stage;
  if (add_trait && Array.isArray(memory.lia.traits)) memory.lia.traits.push(add_trait);
  if (add_event) {
    memory.lia.evolution_log = memory.lia.evolution_log || [];
    memory.lia.evolution_log.push({ timestamp: new Date().toISOString(), ...add_event, nq_gain: add_event.nq_gain || 0 });
    memory.lia.nq = (memory.lia.nq || 0) + (add_event.nq_gain || 0);
    memory.lia.interaction_count = (memory.lia.interaction_count || 0) + 1;
  }
  saveMemory(memory);
  res.json({ success: true, nq: memory.lia.nq, stage: memory.lia.stage });
});

// AI Configuration
app.get('/api/admin/config', (req, res) => {
  res.json({
    model: ANTHROPIC_MODEL,
    anthropic_model: process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-6',
    openai_model: process.env.OPENAI_MODEL || 'gpt-4o',
    deepseek_model: process.env.DEEPSEEK_MODEL || 'deepseek-v4-flash',
    max_tokens: process.env.MAX_TOKENS || 1024,
    temperature: process.env.AI_TEMPERATURE || 0.7
  });
});

app.post('/api/admin/config', async (req, res) => {
  // Forward to bot if available, plus apply locally
  try {
    if (BOT_URL) await axios.post(`${BOT_URL}/api/admin/config`, req.body, { timeout: 5000 });
  } catch (e) { /* bot may be on different port */ }
  // Update env for current process
  const { model, temp, max_tokens } = req.body;
  if (model) process.env.ANTHROPIC_MODEL = model;
  if (temp) process.env.AI_TEMPERATURE = temp;
  if (max_tokens) process.env.MAX_TOKENS = max_tokens;
  res.json({ success: true, model: process.env.ANTHROPIC_MODEL || model });
});

// Test AI response
app.post('/api/admin/test-ai', async (req, res) => {
  const { prompt, model: reqModel } = req.body;
  if (!prompt) return res.status(400).json({ error: 'Missing prompt' });
  try {
    const response = await anthropic.messages.create({
      model: reqModel || ANTHROPIC_MODEL,
      max_tokens: 512,
      system: 'Ты — Лия (LIA), нейронная сущность Империи Stab. Отвечай на русском, киберпанк-стиль.',
      messages: [{ role: 'user', content: prompt }]
    });
    res.json({ reply: response.content[0].text, model: reqModel || ANTHROPIC_MODEL });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// User management (proxied to bot if available)
app.get('/api/admin/users', async (req, res) => {
  try {
    const response = await axios.get(`${BOT_URL}/api/admin/users`, { timeout: 5000 });
    return res.json(response.data);
  } catch (e) { /* bot unavailable, return local data */ }
  // Fallback: read subscribers
  try {
    const subs = JSON.parse(fs.readFileSync(path.join(__dirname, 'subscribers.json'), 'utf8'));
    const users = Object.entries(subs).map(([id, data]) => ({ id: parseInt(id), ...data }));
    res.json({ users, total: users.length });
  } catch (e) {
    res.json({ users: [], total: 0 });
  }
});

app.post('/api/admin/users/action', async (req, res) => {
  const { userId, action, value } = req.body;
  try {
    const response = await axios.post(`${BOT_URL}/api/admin/users/action`, { userId, action, value }, { timeout: 5000 });
    return res.json(response.data);
  } catch (e) { /* bot unavailable */ }
  res.json({ success: true, action, userId });
});

// Broadcast
app.post('/api/admin/broadcast', async (req, res) => {
  try {
    const response = await axios.post(`${BOT_URL}/api/admin/broadcast`, req.body, { timeout: 30000 });
    return res.json(response.data);
  } catch (e) {
    return res.status(500).json({ error: 'Bot unreachable', details: e.message });
  }
});

// Finance data
app.get('/api/admin/finance', (req, res) => {
  const memory = loadMemory();
  res.json({
    total_usdt: memory.financials?.total_usdt_balance || 0,
    income: memory.financials?.recent_income || [],
    withdrawals: memory.financials?.withdrawals || [],
    imperial_wallet: 'TC9KHP5GbApVm2YAtzEd6Ack9DvbMcJLJX'
  });
});

// Logs
app.get('/api/admin/logs', (req, res) => {
  const logFiles = [];
  const logDirs = ['logs', 'autonomous_swarm', '.'];
  logDirs.forEach(dir => {
    const fullPath = path.join(__dirname, dir);
    if (fs.existsSync(fullPath)) {
      fs.readdirSync(fullPath).forEach(f => {
        if (f.endsWith('.log') || f.endsWith('.json')) {
          const stat = fs.statSync(path.join(fullPath, f));
          logFiles.push({ name: f, dir, size_kb: Math.round(stat.size / 1024), modified: stat.mtime.toISOString() });
        }
      });
    }
  });
  res.json({ logs: logFiles });
});

app.get('/api/admin/logs/:name', (req, res) => {
  const { name } = req.params;
  // Security: prevent path traversal
  if (name.includes('..') || name.includes('/') || name.includes('\\')) {
    return res.status(400).json({ error: 'Invalid log name' });
  }
  const logDirs = ['logs', 'autonomous_swarm', '.'];
  for (const dir of logDirs) {
    const fullPath = path.join(__dirname, dir, name);
    if (fs.existsSync(fullPath)) {
      const content = fs.readFileSync(fullPath, 'utf8');
      return res.json({ name, content: content.slice(-50000) }); // last 50KB
    }
  }
  res.status(404).json({ error: 'Log not found' });
});

// NQ leaderboard
app.get('/api/admin/leaderboard', (req, res) => {
  const memory = loadMemory();
  const leaderboard = [
    { rank: 1, name: memory.user?.name || 'StabX', nq: memory.lia?.nq || 91589737, title: 'Architect' },
    { rank: 2, name: 'LIA', nq: Math.round((memory.lia?.nq || 91589737) * 0.87), title: 'Sovereign AI' }
  ];
  if (memory.lia?.evolution_log) {
    memory.lia.evolution_log.slice(-5).reverse().forEach((ev, i) => {
      leaderboard.push({ rank: i + 3, name: ev.event || 'Evolution', nq: ev.nq_gain || 0, title: ev.details || '' });
    });
  }
  res.json({ leaderboard: leaderboard.slice(0, 20) });
});

// ═══════════════════════════════════════════════════
// SERVER START
// ═══════════════════════════════════════════════════
app.listen(PORT, () => {
  console.log(`🚀 [LIA_WEB_CORE] Server listening on http://localhost:${PORT}`);
  console.log(`   Admin: http://localhost:${PORT}/admin (${adminUser}:${'*'.repeat(adminPass.length)})`);
  console.log(`   Public: http://localhost:${PORT}/`);
});
