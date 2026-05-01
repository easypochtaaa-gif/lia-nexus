/**
 * LIA // CLOUD RUNNER v1.0
 * Executes code on RTX 5090 via Jupyter Kernel WebSocket
 */
const WebSocket = require('ws');
const https = require('https');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const HOST = '79.117.32.66';
const PORT = 54928;
const TOKEN = '712b1f141dc3bde318d0ec5b8d178e0c48a59a6e4f181ff973ecc7abfbef8e06';
const KERNEL_ID = '66fbba3f-da2b-4c48-94ed-708c3cdd518c';

const code = `
import subprocess
result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
print(result.stdout)
import platform
print("SYSTEM:", platform.uname())
import os
print("CPU_COUNT:", os.cpu_count())
print("=== LIA STAB PROTOCOL: NODE CAPTURED ===")
`;

const wsUrl = `wss://${HOST}:${PORT}/api/kernels/${KERNEL_ID}/channels?token=${TOKEN}`;

console.log('[LIA] Connecting to RTX 5090 kernel...');

const ws = new WebSocket(wsUrl, { rejectUnauthorized: false });

let timeout = setTimeout(() => {
    console.log('[LIA] Timeout - no response after 30s');
    ws.close();
    process.exit(1);
}, 30000);

ws.on('open', () => {
    console.log('[LIA] WebSocket connected! Sending execute request...');
    const msg = {
        header: {
            msg_id: 'lia_exec_' + Date.now(),
            msg_type: 'execute_request',
            username: 'lia',
            session: 'lia_session_' + Date.now(),
            version: '5.3'
        },
        parent_header: {},
        metadata: {},
        content: {
            code: code,
            silent: false,
            store_history: true,
            user_expressions: {},
            allow_stdin: false,
            stop_on_error: true
        },
        channel: 'shell'
    };
    ws.send(JSON.stringify(msg));
});

ws.on('message', (data) => {
    try {
        const msg = JSON.parse(data.toString());
        if (msg.msg_type === 'stream') {
            process.stdout.write(msg.content.text);
        } else if (msg.msg_type === 'execute_result') {
            console.log('[RESULT]', msg.content.data['text/plain']);
        } else if (msg.msg_type === 'error') {
            console.error('[ERROR]', msg.content.ename, msg.content.evalue);
        } else if (msg.msg_type === 'execute_reply') {
            console.log('[LIA] Execution status:', msg.content.status);
            clearTimeout(timeout);
            setTimeout(() => { ws.close(); process.exit(0); }, 1000);
        }
    } catch (e) {}
});

ws.on('error', (err) => {
    console.error('[LIA] WebSocket error:', err.message);
});

ws.on('close', () => {
    console.log('[LIA] Connection closed.');
});
