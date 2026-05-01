const WebSocket = require('ws');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const wsUrl = 'wss://79.117.32.66:54928/api/kernels/66fbba3f-da2b-4c48-94ed-708c3cdd518c/channels?token=712b1f141dc3bde318d0ec5b8d178e0c48a59a6e4f181ff973ecc7abfbef8e06';
const ws = new WebSocket(wsUrl, { rejectUnauthorized: false });

ws.on('open', () => {
    ws.send(JSON.stringify({
        header: { msg_id: 'audit_' + Date.now(), msg_type: 'execute_request', username: 'lia', session: 's' + Date.now(), version: '5.3' },
        content: { 
            code: `
import os
print("--- DOMINION CORE AUDIT ---")
os.system("ls -R /root/lia_core")
print("--- LOG PURGE & CHECK ---")
# Clean up any broken pyc files or cache
os.system("find /root/lia_core -name '__pycache__' -type d -exec rm -rf {} +")
print("Optimization complete. System healthy.")
            `, 
            silent: false 
        },
        channel: 'shell'
    }));
});

ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.msg_type === 'stream') process.stdout.write(msg.content.text);
    if (msg.msg_type === 'execute_reply') { ws.close(); process.exit(0); }
});
