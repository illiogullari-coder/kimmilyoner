type SoundName =
  | 'intro'
  | 'button'
  | 'joker'
  | 'timer'
  | 'timerFinal'
  | 'correct'
  | 'wrong'
  | 'barrier'
  | 'jackpot'
  | 'final'
  | 'lose'
  | 'win';

class AudioEngine {
  private ctx: AudioContext | null = null;
  private enabled = true;
  private volume = 0.7;
  private activeNodes: Set<AudioNode> = new Set();

  private ensureContext(): AudioContext {
    if (!this.ctx) {
      const Ctor = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new Ctor();
    }
    if (this.ctx.state === 'suspended') void this.ctx.resume();
    return this.ctx;
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (!enabled) this.stopAll();
  }

  setVolume(volume: number): void {
    this.volume = Math.max(0, Math.min(1, volume));
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  getVolume(): number {
    return this.volume;
  }

  private tone(
    freq: number,
    duration: number,
    type: OscillatorType = 'sine',
    startGain = 0.3,
    delay = 0,
  ): void {
    if (!this.enabled) return;
    const ctx = this.ensureContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime + delay);
    gain.gain.setValueAtTime(0, ctx.currentTime + delay);
    gain.gain.linearRampToValueAtTime(startGain * this.volume, ctx.currentTime + delay + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime + delay);
    osc.stop(ctx.currentTime + delay + duration + 0.05);
    this.activeNodes.add(gain);
    osc.onended = () => this.activeNodes.delete(gain);
  }

  private chord(freqs: number[], duration: number, type: OscillatorType = 'sine', gain = 0.2): void {
    freqs.forEach((f) => this.tone(f, duration, type, gain));
  }

  private sequence(notes: { freq: number; dur: number; type?: OscillatorType; gain?: number }[]): void {
    let delay = 0;
    for (const n of notes) {
      this.tone(n.freq, n.dur, n.type ?? 'sine', n.gain ?? 0.3, delay);
      delay += n.dur * 0.9;
    }
  }

  play(name: SoundName): void {
    if (!this.enabled) return;
    switch (name) {
      case 'intro':
        this.sequence([
          { freq: 392, dur: 0.25, type: 'triangle' },
          { freq: 523, dur: 0.25, type: 'triangle' },
          { freq: 659, dur: 0.25, type: 'triangle' },
          { freq: 784, dur: 0.5, type: 'triangle' },
        ]);
        break;
      case 'button':
        this.tone(880, 0.08, 'square', 0.15);
        break;
      case 'joker':
        this.sequence([
          { freq: 660, dur: 0.12, type: 'sawtooth', gain: 0.2 },
          { freq: 880, dur: 0.12, type: 'sawtooth', gain: 0.2 },
          { freq: 1100, dur: 0.2, type: 'sawtooth', gain: 0.2 },
        ]);
        break;
      case 'timer':
        this.tone(440, 0.1, 'sine', 0.2);
        break;
      case 'timerFinal':
        this.tone(880, 0.12, 'square', 0.3);
        break;
      case 'correct':
        this.sequence([
          { freq: 523, dur: 0.12, type: 'triangle', gain: 0.25 },
          { freq: 659, dur: 0.12, type: 'triangle', gain: 0.25 },
          { freq: 784, dur: 0.3, type: 'triangle', gain: 0.3 },
        ]);
        break;
      case 'wrong':
        this.sequence([
          { freq: 220, dur: 0.2, type: 'sawtooth', gain: 0.25 },
          { freq: 180, dur: 0.4, type: 'sawtooth', gain: 0.25 },
        ]);
        break;
      case 'barrier':
        this.chord([523, 659, 784], 0.5, 'triangle', 0.2);
        break;
      case 'jackpot':
        this.sequence([
          { freq: 523, dur: 0.15, type: 'triangle', gain: 0.25 },
          { freq: 659, dur: 0.15, type: 'triangle', gain: 0.25 },
          { freq: 784, dur: 0.15, type: 'triangle', gain: 0.25 },
          { freq: 1047, dur: 0.4, type: 'triangle', gain: 0.3 },
        ]);
        break;
      case 'final':
        this.sequence([
          { freq: 440, dur: 0.2, type: 'sawtooth', gain: 0.2 },
          { freq: 554, dur: 0.2, type: 'sawtooth', gain: 0.2 },
          { freq: 659, dur: 0.4, type: 'sawtooth', gain: 0.25 },
        ]);
        break;
      case 'lose':
        this.sequence([
          { freq: 330, dur: 0.3, type: 'sawtooth', gain: 0.25 },
          { freq: 262, dur: 0.3, type: 'sawtooth', gain: 0.25 },
          { freq: 196, dur: 0.6, type: 'sawtooth', gain: 0.25 },
        ]);
        break;
      case 'win':
        this.sequence([
          { freq: 523, dur: 0.15, type: 'triangle', gain: 0.3 },
          { freq: 659, dur: 0.15, type: 'triangle', gain: 0.3 },
          { freq: 784, dur: 0.15, type: 'triangle', gain: 0.3 },
          { freq: 1047, dur: 0.15, type: 'triangle', gain: 0.3 },
          { freq: 1319, dur: 0.5, type: 'triangle', gain: 0.35 },
        ]);
        break;
    }
  }

  stopAll(): void {
    this.activeNodes.forEach((n) => {
      try {
        if ('stop' in n && typeof (n as { stop: () => void }).stop === 'function') {
          (n as { stop: () => void }).stop();
        }
      } catch {
        /* noop */
      }
    });
    this.activeNodes.clear();
  }

  resume(): void {
    if (this.ctx && this.ctx.state === 'suspended') void this.ctx.resume();
  }
}

export const audio = new AudioEngine();
