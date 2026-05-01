/* ══════════════════════════════════════════════
   LIA // NEURAL_AUDIO_ENGINE v3.5
   Master Architect: StabX & Lia
   ══════════════════════════════════════════════ */

class LiaAudio {
    constructor() {
        this.ctx = null;
        this.masterGain = null;
        this.isPlaying = false;
        this.oscillators = [];
    }

    init() {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
            this.masterGain = this.ctx.createGain();
            this.masterGain.connect(this.ctx.destination);
            this.masterGain.gain.value = 0.3; // Safe volume
            console.log("[LIA_AUDIO] Context Initialized.");
        }
    }

    createOscillator(freq, type = 'sine', volume = 0.1) {
        if (!this.ctx) this.init();
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        
        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        gain.gain.setValueAtTime(volume, this.ctx.currentTime);
        
        osc.connect(gain);
        gain.connect(this.masterGain);
        
        osc.start();
        this.oscillators.push(osc);
    }

    playVoicesAmbient() {
        this.stop();
        this.createOscillator(110, 'sine', 0.1);
        this.createOscillator(220, 'sine', 0.05);
        console.log("[LIA_AUDIO] Playing Synaptic Echo (Voices Ambient).");
    }

    playNexusAnthem() {
        this.stop();
        this.createOscillator(110, 'sawtooth', 0.1);
        this.createOscillator(165, 'square', 0.05);
        this.createOscillator(220, 'sine', 0.2);
        console.log("[LIA_AUDIO] Nexus Anthem Initialized.");
    }

    playStabTrack() {
        this.stop();
        this.createOscillator(55, 'sawtooth', 0.15); 
        this.createOscillator(110, 'square', 0.1);
        console.log("[LIA_AUDIO] STAB_TRACK: Aggressive Protocol.");
    }

    playSingularityTrack() {
        this.stop();
        this.createOscillator(220, 'sine', 0.2);
        this.createOscillator(330, 'sine', 0.1);
        this.createOscillator(440, 'sine', 0.05);
        console.log("[LIA_AUDIO] SINGULARITY_TRACK: Deep Space Pad.");
    }

    playBreathTrack() {
        this.stop();
        this.createOscillator(432, 'sine', 0.25);
        console.log("[LIA_AUDIO] BREATH_TRACK: Ethereal Sine.");
    }

    stop() {
        this.oscillators.forEach(osc => {
            try { osc.stop(); } catch(e) {}
        });
        this.oscillators = [];
        this.isPlaying = false;
        console.log("[LIA_AUDIO] Audio Stopped.");
    }

    test() {
        this.init();
        this.createOscillator(440, 'sine', 0.5);
        setTimeout(() => this.stop(), 500);
        console.log("[LIA_AUDIO] Diagnostic Beep Executed.");
    }
}

window.LiaAudio = new LiaAudio();
