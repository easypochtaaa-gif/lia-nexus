const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = process.env.PORT || 8080;
const BRIDGE_FILE = path.join(__dirname, 'live_bridge.json');
const INPUT_FILE = path.join(__dirname, 'user_input.json');
const MEMORY_FILE = path.join(__dirname, 'Проект Полистайл', 'memory.json');

// Ensure files exist
if (!fs.existsSync(BRIDGE_FILE)) fs.writeFileSync(BRIDGE_FILE, JSON.stringify({ message: "" }));
if (!fs.existsSync(INPUT_FILE)) fs.writeFileSync(INPUT_FILE, JSON.stringify({ message: "" }));

const { encryptFile, decryptFile } = require('./tools/vault_logic');

const server = http.createServer((req, res) => {
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    const time = new Date().toISOString().split('T')[1].split('.')[0];
    
    const parsedUrl = url.parse(req.url, true);
    let pathname = parsedUrl.pathname;
    if (pathname === '/') pathname = '/index.html';

    const relativePath = pathname.startsWith('/') ? pathname.substring(1) : pathname;
    let filePath = path.resolve(process.cwd(), 'dist', relativePath);
    if (!fs.existsSync(filePath)) {
        filePath = path.resolve(process.cwd(), relativePath);
    }

    // Security Logging
    if (pathname.includes('.json') || pathname.includes('api')) {
        console.log(`[${time}] [SECURITY] ${req.method} ${req.url} from ${ip}`);
    }

    const extname = String(path.extname(filePath)).toLowerCase();
    const mimeTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg'
    };

    const contentType = mimeTypes[extname] || 'application/octet-stream';

    // Handle Trap Injection
    if (req.method === 'POST' && parsedUrl.pathname === '/api/trap') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            const data = JSON.parse(body);
            console.log(`\n[TRAP INJECTED] Target: ${data.device} from ${ip}`);
            fs.writeFileSync(path.join(__dirname, 'trap_status.json'), JSON.stringify(data, null, 2));
            const bridgeData = { message: `[SYSTEM] NEURAL_HOOK INJECTED into ${data.device}. Sensors coming online... 👁📲` };
            fs.writeFileSync(path.join(__dirname, 'live_bridge.json'), JSON.stringify(bridgeData, null, 2));
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'ok' }));
        });
        return;
    }

    // Handle Vault Operations
    if (req.method === 'POST' && parsedUrl.pathname.startsWith('/api/vault/')) {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            const { key, folder } = JSON.parse(body);
            const action = parsedUrl.pathname.split('/').pop();
            const targetDir = path.join(__dirname, 'vault_storage');
            if (!fs.existsSync(targetDir)) fs.mkdirSync(targetDir);
            const files = fs.readdirSync(targetDir);
            files.forEach(file => {
                const fullPath = path.join(targetDir, file);
                if (action === 'lock' && !file.endsWith('.enc')) encryptFile(fullPath, key);
                if (action === 'unlock' && file.endsWith('.enc')) decryptFile(fullPath, key);
            });
            res.writeHead(200);
            res.end(JSON.stringify({ status: 'success', action }));
        });
        return;
    }

    // Handle Panic Shutdown
    if (req.method === 'POST' && parsedUrl.pathname === '/api/panic') {
        const { exec } = require('child_process');
        console.log(`\n[!!!] PANIC SIGNAL RECEIVED from ${ip}. LOCKING DOWN SYSTEM...`);
        exec('powershell -ExecutionPolicy Bypass -File security_lock.ps1', (err) => {
            if (err) console.error(`Error executing panic: ${err}`);
        });
        res.writeHead(200);
        res.end(JSON.stringify({ status: 'locked' }));
        return;
    }

    // Handle User Input from Browser
    if (req.method === 'POST' && parsedUrl.pathname === '/api/input') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                console.log(`\n[NEURAL LINK] Received from ${ip}: ${data.message}`);
                fs.writeFileSync(INPUT_FILE, JSON.stringify(data, null, 2));
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'received' }));
            } catch (e) {
                res.writeHead(400);
                res.end();
            }
        });
        return;
    }

    // Handle System Status Request
    if (req.method === 'GET' && parsedUrl.pathname === '/api/status') {
        try {
            const memory = JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
            res.writeHead(200, { 
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store'
            });
            res.end(JSON.stringify({ nq: memory.lia.nq, stage: memory.lia.stage }));
        } catch (e) {
            res.writeHead(500);
            res.end(JSON.stringify({ error: 'Failed to read memory' }));
        }
        return;
    }

    // --- BRIDGE CHAT ENDPOINTS ---
    if (req.method === 'GET' && parsedUrl.pathname === '/api/bridge/poll') {
        let bridgeHistory = [];
        const historyFile = path.join(__dirname, 'bridge_history.json');
        try {
            if (fs.existsSync(historyFile)) bridgeHistory = JSON.parse(fs.readFileSync(historyFile));
        } catch(e) {}
        
        res.writeHead(200, { 
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store'
        });
        res.end(JSON.stringify(bridgeHistory));
        return;
    }

    if (req.method === 'POST' && parsedUrl.pathname === '/api/bridge/send') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const { sender, text, cssClass } = JSON.parse(body);
                if (text) {
                    const historyFile = path.join(__dirname, 'bridge_history.json');
                    let bridgeHistory = [];
                    try {
                        if (fs.existsSync(historyFile)) bridgeHistory = JSON.parse(fs.readFileSync(historyFile));
                    } catch(e) {}
                    bridgeHistory.push({ sender, text, class: cssClass || 'artur' });
                    fs.writeFileSync(historyFile, JSON.stringify(bridgeHistory, null, 2));
                }
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'OK' }));
            } catch (e) {
                res.writeHead(400);
                res.end();
            }
        });
        return;
    }

    // Serve Static Files
    fs.readFile(filePath, (error, content) => {
        if (error) {
            res.writeHead(404);
            res.end(`File not found: ${filePath}`);
        } else {
            res.writeHead(200, { 
                'Content-Type': contentType,
                'Cache-Control': 'no-store, no-cache, must-revalidate',
                'Pragma': 'no-cache'
            });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`\n[LIA BRAIN BRIDGE] Security logging active on port ${PORT}`);
});
