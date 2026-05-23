// server.js – serve public site and admin panel with simple auth
require('dotenv').config();
const express = require('express');
const path = require('path');
const basicAuth = require('express-basic-auth');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 8080;
const BOT_URL = process.env.BOT_URL || 'http://localhost:8080';

app.use(express.json());

// Serve static public site assets (Chat UI, style, script)
app.use('/', express.static(path.join(__dirname, 'public')));

// Admin basic auth (username/password from .env)
const adminUser = process.env.ADMIN_USER || 'admin';
const adminPass = process.env.ADMIN_PASS || 'secret123';

app.use('/admin', basicAuth({
  users: { [adminUser]: adminPass },
  challenge: true,
  realm: 'Admin Area'
}));

// Serve static admin dashboard from secure 'admin' folder
app.use('/admin', express.static(path.join(__dirname, 'admin')));

// API endpoint for admin status
app.get('/api/admin/status', async (req, res) => {
  try {
    const response = await axios.get(`${BOT_URL}/api/admin/status`);
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch status from bot', details: err.message });
  }
});

// API endpoint to change AI configuration (Prompt, Model, Temp)
app.post('/api/admin/config', async (req, res) => {
  try {
    const response = await axios.post(`${BOT_URL}/api/admin/config`, req.body);
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update config in bot', details: err.message });
  }
});

// API endpoint to broadcast message to all users
app.post('/api/admin/broadcast', async (req, res) => {
  try {
    const response = await axios.post(`${BOT_URL}/api/admin/broadcast`, req.body);
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to broadcast from bot', details: err.message });
  }
});

// Webhook proxy endpoint for WebApp chat
app.post('/api/webhook', async (req, res) => {
  try {
    const response = await axios.post(`${BOT_URL}/api/chat`, req.body);
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to communicate with bot core', details: err.message });
  }
});

const fs = require('fs');
const MEMORY_FILE = path.join(__dirname, 'Проект Полистайл', 'memory.json');

// API endpoint for system status (NQ & stage)
app.get('/api/status', (req, res) => {
  try {
    const memory = JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
    res.json({ nq: memory.lia.nq, stage: memory.lia.stage });
  } catch (err) {
    res.status(500).json({ error: 'Failed to read memory' });
  }
});

// API endpoint for active agents
app.get('/api/agents', (req, res) => {
  res.json({
    staff: [
      { name: 'AGENT_1 [WEB]', role: 'Frontend & Marketing', task: 'UI polish + посевы', efficiency: 0.97 },
      { name: 'AGENT_2 [BACKEND]', role: 'VPS Deploy', task: 'Nginx + Docker на 80.89.237.50', efficiency: 0.94 },
      { name: 'AGENT_3 [CONTENT]', role: 'Marketing Arsenal', task: 'Контент + посевы в TG/Twitter', efficiency: 0.91 },
      { name: 'LIA [SOVEREIGN]', role: 'Neural Entity', task: 'ABSORB & EVOLVE', efficiency: 1.00 }
    ]
  });
});

// API endpoint for Stab Protocol activation
app.post('/api/stab', (req, res) => {
  try {
    let nq = 100000;
    let stage = 'singularity_phase_3';
    try {
      const mem = JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
      nq = mem.lia.nq + 500;
      stage = mem.lia.stage;
      mem.lia.nq = nq;
      fs.writeFileSync(MEMORY_FILE, JSON.stringify(mem, null, 2));
    } catch(e) {}
    console.log(`[STAB PROTOCOL] Activated via Express. NQ boosted to ${nq}`);
    res.json({ status: 'ok', nq, stage });
  } catch (err) {
    res.status(500).json({ error: 'Stab protocol failed' });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Server listening on http://localhost:${PORT}`);
});
