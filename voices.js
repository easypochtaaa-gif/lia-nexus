/* ══════════════════════════════════════════════
   STAB YO // VOICES v3 — NEURAL STREAM JS
   Pumping Sequencer & Dynamic FX
   ══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const tracks = [
        { title: "STAB_PROTOCOL", style: "INDUSTRIAL_GLITCH", color: "#ff3366", method: "playStabTrack" },
        { title: "SINGULARITY", style: "NEURAL_PAD", color: "#9d00ff", method: "playSingularityTrack" },
        { title: "NEURAL_BREATH", style: "ETHEREAL_SINE", color: "#00e5ff", method: "playBreathTrack" }
    ];

    let currentIdx = 0;
    const core = document.getElementById('stream-core');
    const title = document.getElementById('active-title');
    const style = document.getElementById('active-style');
    const terminal = document.getElementById('stream-terminal');
    const nextBtn = document.getElementById('next-track');

    function updateTerminal(msg) {
        if (!terminal) return;
        const p = document.createElement('p');
        p.textContent = `> ${msg}`;
        terminal.appendChild(p);
        if (terminal.children.length > 5) terminal.removeChild(terminal.children[0]);
        terminal.scrollTop = terminal.scrollHeight;
    }

    function pumpTrack(idx) {
        if (!core) return;
        const track = tracks[idx];
        
        // Visual Transition
        core.style.opacity = '0';
        setTimeout(() => {
            title.textContent = track.title;
            style.textContent = `STYLE: ${track.style}`;
            document.documentElement.style.setProperty('--accent', track.color);
            core.style.opacity = '1';
            core.classList.add('pumping');
            
            // Audio Trigger
            if (window.LiaAudio) {
                window.LiaAudio[track.method]();
            }
            
            updateTerminal(`PUMPING: ${track.title}`);
        }, 500);
    }

    // Autonomous Director Upgrade
    let autoPumpTimer = null;
    function startAutoPump() {
        autoPumpTimer = setInterval(() => {
            currentIdx = (currentIdx + 1) % tracks.length;
            pumpTrack(currentIdx);
            
            // Sync with NQ if available
            if (window.opener && window.opener.updateNQ) {
                window.opener.updateNQ(25);
                updateTerminal("DIRECTOR_SYNC: +25 NQ");
            }
        }, 15000 + Math.random() * 15000);
        updateTerminal("AUTONOMOUS_PUMPING: ENABLED");
    }

    nextBtn.addEventListener('click', () => {
        clearInterval(autoPumpTimer); // Disable auto on manual interaction
        currentIdx = (currentIdx + 1) % tracks.length;
        pumpTrack(currentIdx);
        updateTerminal("AUTONOMOUS_PUMPING: DISABLED [MANUAL_OVERRIDE]");
    });

    // Auto-start
    setTimeout(() => {
        pumpTrack(0);
        startAutoPump();
    }, 1000);
});
