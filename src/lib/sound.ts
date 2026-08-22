/**
 * Small synthesised interface sounds. Generated with the Web Audio API rather
 * than shipped as files, so the builder stays light and nothing extra loads.
 */

let context: AudioContext | null = null;

function ctx(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!context) {
    const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return null;
    context = new Ctor();
  }
  // Browsers start the context suspended until a gesture; clicks resume it.
  if (context.state === "suspended") void context.resume();
  return context;
}

/** A short filtered noise burst: the mechanical part of a bolt moving. */
function clack(at: number, gain: number, cutoff: number) {
  const c = ctx();
  if (!c) return;
  const length = Math.floor(c.sampleRate * 0.06);
  const buffer = c.createBuffer(1, length, c.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < length; i++) {
    // Decaying noise, sharp at the front like metal striking metal.
    data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 3.5);
  }
  const source = c.createBufferSource();
  source.buffer = buffer;

  const filter = c.createBiquadFilter();
  filter.type = "bandpass";
  filter.frequency.value = cutoff;
  filter.Q.value = 1.2;

  const amp = c.createGain();
  amp.gain.value = gain;

  source.connect(filter).connect(amp).connect(c.destination);
  source.start(at);
}

/** A soft tone under the clack, so the action reads as confirmed. */
function tone(at: number, frequency: number, gain: number, duration = 0.12) {
  const c = ctx();
  if (!c) return;
  const osc = c.createOscillator();
  osc.type = "sine";
  osc.frequency.setValueAtTime(frequency, at);

  const amp = c.createGain();
  amp.gain.setValueAtTime(0, at);
  amp.gain.linearRampToValueAtTime(gain, at + 0.012);
  amp.gain.exponentialRampToValueAtTime(0.0001, at + duration);

  osc.connect(amp).connect(c.destination);
  osc.start(at);
  osc.stop(at + duration + 0.02);
}

/** Deadbolt driving home: two quick clacks and a low thunk. */
export function playLock() {
  const c = ctx();
  if (!c) return;
  const t = c.currentTime;
  clack(t, 0.32, 1800);
  clack(t + 0.055, 0.24, 1200);
  tone(t + 0.05, 180, 0.1, 0.16);
}

/** Bolt withdrawing: a lighter clack and a rising confirmation. */
export function playUnlock() {
  const c = ctx();
  if (!c) return;
  const t = c.currentTime;
  clack(t, 0.26, 2400);
  tone(t + 0.03, 520, 0.075, 0.1);
  tone(t + 0.11, 760, 0.06, 0.12);
}

/** Quiet motor hum for curtains moving. */
export function playCurtain() {
  const c = ctx();
  if (!c) return;
  const t = c.currentTime;
  const osc = c.createOscillator();
  osc.type = "sawtooth";
  osc.frequency.setValueAtTime(120, t);

  const filter = c.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = 700;

  const amp = c.createGain();
  amp.gain.setValueAtTime(0, t);
  amp.gain.linearRampToValueAtTime(0.045, t + 0.06);
  amp.gain.setValueAtTime(0.045, t + 0.42);
  amp.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);

  osc.connect(filter).connect(amp).connect(c.destination);
  osc.start(t);
  osc.stop(t + 0.62);
}
