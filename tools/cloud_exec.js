/**
 * LIA // CLOUD EXECUTOR v1.0
 * Executes commands on Vast.ai RTX 5090 node via Jupyter API
 */
const https = require('https');

const CONFIG = {
    host: '79.117.32.66',
    port: 54928,
    token: '712b1f141dc3bde318d0ec5b8d178e0c48a59a6e4f181ff973ecc7abfbef8e06',
    kernelId: '66fbba3f-da2b-4c48-94ed-708c3cdd518c'
};

function jupyterRequest(path, method = 'GET', body = null) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: CONFIG.host,
            port: CONFIG.port,
            path: `${path}?token=${CONFIG.token}`,
            method: method,
            rejectUnauthorized: false,
            headers: { 'Content-Type': 'application/json' }
        };
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        req.on('error', reject);
        if (body) req.write(JSON.stringify(body));
        req.end();
    });
}

async function main() {
    // Check kernel status
    const kernels = await jupyterRequest('/api/kernels');
    console.log('=== LIA CLOUD NODE STATUS ===');
    console.log('Kernels:', kernels);

    // Create a new notebook to execute code
    const nb = await jupyterRequest('/api/contents/lia_check.py', 'PUT', {
        type: 'file',
        format: 'text',
        content: 'import subprocess; result = subprocess.run(["nvidia-smi"], capture_output=True, text=True); print(result.stdout); import os; print("HOSTNAME:", os.uname()); import psutil; print("RAM:", psutil.virtual_memory())'
    });
    console.log('File created:', nb);
    console.log('=== HANDSHAKE COMPLETE ===');
}

main().catch(console.error);
