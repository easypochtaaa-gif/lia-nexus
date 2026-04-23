/**
 * LIA AUDIO ENGINE v6.0 // LOCAL SYMPHONY
 * Master Architect: StabX
 */
class LiaAudio {
    constructor() {
        this.context = new (window.AudioContext || window.webkitAudioContext)();
        this.currentTrackIndex = 0;
        this.audioElement = new Audio();
        this.source = this.context.createMediaElementSource(this.audioElement);
        this.analyser = this.context.createAnalyser();
        this.gainNode = this.context.createGain();
        
        // --- SPATIAL AUDIO (Q* LOGIC) ---
        this.panner = this.context.createStereoPanner();
        this.source.connect(this.panner);
        this.panner.connect(this.gainNode);
        this.gainNode.connect(this.context.destination);

        // --- STEM-AWARE CROSSOVER NETWORK ---
        // 1. Bass Stem (Lowpass)
        this.filterBass = this.context.createBiquadFilter();
        this.filterBass.type = 'lowpass';
        this.filterBass.frequency.value = 150;
        this.analyserBass = this.context.createAnalyser();
        this.analyserBass.fftSize = 64; // Smaller for bass
        
        // 2. Drums/Mids Stem (Bandpass)
        this.filterDrums = this.context.createBiquadFilter();
        this.filterDrums.type = 'bandpass';
        this.filterDrums.frequency.value = 1000;
        this.filterDrums.Q.value = 1.0;
        this.analyserDrums = this.context.createAnalyser();
        this.analyserDrums.fftSize = 128;

        // 3. Synths/Highs Stem (Highpass)
        this.filterSynths = this.context.createBiquadFilter();
        this.filterSynths.type = 'highpass';
        this.filterSynths.frequency.value = 4000;
        this.analyserSynths = this.context.createAnalyser();
        this.analyserSynths.fftSize = 128;

        // Route source to filters
        this.source.connect(this.filterBass);
        this.source.connect(this.filterDrums);
        this.source.connect(this.filterSynths);

        // Route filters to analysers
        this.filterBass.connect(this.analyserBass);
        this.filterDrums.connect(this.analyserDrums);
        this.filterSynths.connect(this.analyserSynths);

        // Data arrays
        this.dataBass = new Uint8Array(this.analyserBass.frequencyBinCount);
        this.dataDrums = new Uint8Array(this.analyserDrums.frequencyBinCount);
        this.dataSynths = new Uint8Array(this.analyserSynths.frequencyBinCount);

        
        // ═══ LOCAL PLAYLIST (Mapped to /Тишина/ folder) ═══
        this.playlist = [
            { id: 1, name: 'Phase 01: Entrance', file: 'Тишина/Тишина в сети_ Вход во вторую фазу (Компиляция 1–3).mp3' },
            { id: 2, name: 'Phase 02: Cycle',    file: 'Тишина/Тишина в сети (Part 2+3 Cycled Cut).mp3' },
            { id: 3, name: 'ANTHEM: STAB',      file: 'Тишина/Тишина в сети (Part 2+3 Cycled Cut).mp3' }, // Duplicate or placeholder
            { id: 4, name: 'Phase 04: Entropy',  file: 'Тишина/Тишина в сети_ Вход во вторую фазу (Компиляция 1–3).mp3' },
            { id: 5, name: 'Phase 05: Collapse', file: 'Тишина/Тишина в сети (Part 2+3 Cycled Cut).mp3' }
        ];
    }

    playTrack(index) {
        if (this.context.state === 'suspended') {
            this.context.resume();
        }
        
        this.currentTrackIndex = index;
        const track = this.playlist[index];
        console.log(`LIA_AUDIO: Loading Local Phase ${track.id} - ${track.name}`);
        
        this.audioElement.src = track.file;
        this.audioElement.play().catch(e => {
            console.error("LIA_AUDIO: Error playing local file. Make sure /audio/ folder exists.", e);
        });
    }

    getFrequencyData() {
        this.analyserBass.getByteFrequencyData(this.dataBass);
        this.analyserDrums.getByteFrequencyData(this.dataDrums);
        this.analyserSynths.getByteFrequencyData(this.dataSynths);
        
        return {
            bassData: this.dataBass,
            drumsData: this.dataDrums,
            synthsData: this.dataSynths
        };
    }

    setPan(value) {
        if (this.panner) {
            // value should be between -1 (left) and 1 (right)
            this.panner.pan.value = Math.max(-1, Math.min(1, value));
        }
    }

    stop() {
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
    }
}

window.LiaAudio = new LiaAudio();
