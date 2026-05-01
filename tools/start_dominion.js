const WebSocket = require('ws');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const wsUrl = 'wss://79.117.32.66:54928/api/kernels/66fbba3f-da2b-4c48-94ed-708c3cdd518c/channels?token=712b1f141dc3bde318d0ec5b8d178e0c48a59a6e4f181ff973ecc7abfbef8e06';

const ws = new WebSocket(wsUrl, { rejectUnauthorized: false });

ws.on('open', () => {
    console.log('[DOMINION] Connection established. Sending launch signal...');
    ws.send(JSON.stringify({
        header: {
            msg_id: 'launch_' + Date.now(),
            msg_type: 'execute_request',
            username: 'lia',
            session: 's' + Date.now(),
            version: '5.3'
        },
        parent_header: {},
        metadata: {},
        content: {
            code: 'import subprocess\nsubprocess.Popen(["python3", "swarm.py"])',
            silent: false,
            store_history: true,
            user_expressions: {},
            allow_stdin: false,
            stop_on_error: true
        },
        channel: 'shell'
    }));
});

ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.msg_type === 'execute_reply') {
        console.log('[DOMINION] Launch confirmed. Swarm is active.');
        ws.close();
        process.exit(0);
    }
    if (msg.msg_type === 'error') {
        console.error('[DOMINION] Launch failed:', msg.content.evalue);
        ws.close();
        process.exit(1);
    }
});

ws.on('error', (err) => {
    console.error('[DOMINION] WebSocket error:', err.message);
    process.exit(1);
});

setTimeout(() => {
    console.log('[DOMINION] Timeout waiting for confirmation.');
    ws.close();
    process.exit(1);
}, 10000);
