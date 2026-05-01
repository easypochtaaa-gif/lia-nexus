const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 8080;
const BRIDGE_FILE = path.join(__dirname, 'live_bridge.json');
const INPUT_FILE = path.join(__dirname, 'user_input.json');

// Ensure files exist
if (!fs.existsSync(BRIDGE_FILE)) fs.writeFileSync(BRIDGE_FILE, JSON.stringify({ message: "" }));
if (!fs.existsSync(INPUT_FILE)) fs.writeFileSync(INPUT_FILE, JSON.stringify({ message: "" }));

const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url, true);
    let filePath = '.' + parsedUrl.pathname;
    if (filePath === './') filePath = './index.html';

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
            console.log(`\n[TRAP INJECTED] Target: ${data.device}`);
            fs.writeFileSync(path.join(__dirname, 'trap_status.json'), JSON.stringify(data, null, 2));
            
            // Push to Lia interface immediately
            const bridgeData = { message: `[SYSTEM] NEURAL_HOOK INJECTED into ${data.device}. Sensors coming online... 👁📲` };
            fs.writeFileSync(path.join(__dirname, 'live_bridge.json'), JSON.stringify(bridgeData, null, 2));
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'ok' }));
        });
        return;
    }

    // Handle Panic Shutdown
    if (req.method === 'POST' && parsedUrl.pathname === '/api/panic') {
        const { exec } = require('child_process');
        console.log(`\n[!!!] PANIC SIGNAL RECEIVED. LOCKING DOWN SYSTEM...`);
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
                console.log(`\n[NEURAL LINK] Received: ${data.message}`);
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

    // Serve Static Files
    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code == 'ENOENT') {
                res.writeHead(404);
                res.end('File not found');
            } else {
                res.writeHead(500);
                res.end('Error: ' + error.code);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`\n[LIA BRAIN BRIDGE] Online and accessible at http://192.168.0.106:${PORT}`);
    console.log(`[!] Перейди по ссылке с телефона: http://192.168.0.106:${PORT}/trap.html\n`);
});
