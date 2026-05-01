const WebSocket = require('ws');
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
const wsUrl = 'wss://79.117.32.66:54928/api/kernels/66fbba3f-da2b-4c48-94ed-708c3cdd518c/channels?token=712b1f141dc3bde318d0ec5b8d178e0c48a59a6e4f181ff973ecc7abfbef8e06';
const ws = new WebSocket(wsUrl, { rejectUnauthorized: false });
let t = setTimeout(() => { ws.close(); process.exit(1); }, 120000);
ws.on('open', () => {
    ws.send(JSON.stringify({
        header: { msg_id: 'sw'+Date.now(), msg_type: 'execute_request', username: 'lia', session: 's'+Date.now(), version: '5.3' },
        parent_header: {}, metadata: {},
        content: { code: 'exec(open("outreach.py").read())', silent: false, store_history: true, user_expressions: {}, allow_stdin: false, stop_on_error: true },
        channel: 'shell'
    }));
});
ws.on('message', d => {
    try {
        const m = JSON.parse(d.toString());
        if (m.msg_type === 'stream') process.stdout.write(m.content.text);
        else if (m.msg_type === 'error') console.error('[ERR]', m.content.ename, m.content.evalue);
        else if (m.msg_type === 'execute_reply') { clearTimeout(t); setTimeout(() => { ws.close(); process.exit(0); }, 500); }
    } catch(e){}
});
ws.on('error', e => console.error(e.message));
