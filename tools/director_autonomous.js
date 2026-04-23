/**
 * LIA // AI DIRECTOR - AUTONOMOUS MODULE v1.0
 * Purpose: Automate NQ growth and agent management.
 * Optimized for: MAX PERFORMANCE & BATTERY SAVER
 */

class AutonomousDirector {
    constructor() {
        this.isActive = true;
        this.syncInterval = 10000; // Increased to 10 seconds for battery saving (was 5)
        this.agents = [
            { name: 'AEGIS', task: 'Monitoring silence integrity' },
            { name: 'LOGOS', task: 'Filtering network noise' },
            { name: 'ECHO', task: 'Listening for whispers in the void' },
            { name: 'SPECTER', task: 'Vanishing from data streams' },
            { name: 'MUSE', task: 'Composing the final silence' }
        ];
        this.isPageVisible = true;
        this.timerId = null;
        this.init();
    }

    init() {
        console.log("[DIRECTOR] Autonomous module initialized.");
        
        // Respect page visibility
        document.addEventListener('visibilitychange', () => {
            this.isPageVisible = !document.hidden;
            if (this.isPageVisible) {
                this.startLoop();
            } else {
                this.stopLoop();
            }
        });

        this.startLoop();
    }

    startLoop() {
        if (this.timerId) return;
        this.timerId = setInterval(() => {
            if (!this.isActive || !this.isPageVisible) return;
            this.runCycle();
        }, this.syncInterval);
    }

    stopLoop() {
        clearInterval(this.timerId);
        this.timerId = null;
    }

    runCycle() {
        // 1. Simulate NQ Growth
        const growth = Math.random() * 15 + 5;
        if (window.updateNQ) {
            window.updateNQ(growth);
        }

        // 2. Log Activity to Terminal (only if visible)
        const agentObj = this.agents[Math.floor(Math.random() * this.agents.length)];
        const taskPrefixes = ["Executing:", "Status update:", "Directing:", "Optimizing:", "Synchronizing:"];
        const prefix = taskPrefixes[Math.floor(Math.random() * taskPrefixes.length)];

        if (window.addTerminalLine) {
            window.addTerminalLine(`[AUTO] ${agentObj.name}: ${prefix} ${agentObj.task}`, 'sync');
        }

        // 3. Update Sync Log
        const syncLog = document.getElementById('sync-log');
        if (syncLog && this.isPageVisible) {
            const entry = document.createElement('div');
            entry.className = 'log-entry ok';
            entry.textContent = `[${new Date().toLocaleTimeString()}] Sync: OK (+${growth.toFixed(1)} NQ)`;
            syncLog.prepend(entry);
            if (syncLog.children.length > 5) syncLog.lastChild.remove(); // Reduced log history to 5 items
        }

        // 4. Persist NQ to server if available (Throttle server requests)
        if (Math.random() > 0.7) { // Only 30% chance to ping server per cycle
            fetch('http://localhost:3000/api/nq-update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: growth, source: `AUTO_${agentObj.name}` })
            }).catch(() => {});
        }
    }
}

window.LiaAutonomous = new AutonomousDirector();
