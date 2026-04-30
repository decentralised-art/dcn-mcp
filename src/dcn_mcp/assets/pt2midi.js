#!/usr/bin/env node
// Usage: node tools/pt2midi.js <input_json> <output_mid>
// <input_json> can be either:
//   - stitched payload object with { tracks: ... }
//   - flat array of {path,data} or {feature_path,data} items

const fs = require('fs');
const path = require('path');
const JZZ = require('jzz');
require('jzz-midi-smf')(JZZ);

const CHANNELS = Array.from({ length: 16 }, (_, i) => i).filter((c) => c !== 9);
const DEFAULT_GM_PROGRAMS = {
  composition: 0
};

function metaFor(instrKey, instrumentMeta) {
  const m = (instrumentMeta || {})[instrKey] || {};
  const fallbackProgram = Number.isInteger(DEFAULT_GM_PROGRAMS[instrKey]) ? DEFAULT_GM_PROGRAMS[instrKey] : 0;
  return {
    name: m.display_name || instrKey,
    program: Number.isInteger(m.gm_program) ? m.gm_program : fallbackProgram,
    bankMSB: Number.isInteger(m.bank_msb) ? m.bank_msb : (Number.isInteger(m.bank) ? m.bank : 0),
    bankLSB: Number.isInteger(m.bank_lsb) ? m.bank_lsb : 0
  };
}

function deriveInstrOrder(payload) {
  if (payload && Array.isArray(payload.ordered_instruments) && payload.ordered_instruments.length) {
    return payload.ordered_instruments;
  }
  if (payload && payload.instrument_meta && typeof payload.instrument_meta === 'object') {
    return Object.keys(payload.instrument_meta);
  }
  if (payload && payload.tracks && typeof payload.tracks === 'object') {
    return Object.keys(payload.tracks);
  }
  return ['composition'];
}

function samplePath(item) {
  if (!item || typeof item !== 'object') return '';
  return item.path || item.feature_path || '';
}

function normalizeScalarName(name) {
  const raw = String(name || '').trim().toLowerCase();
  const base = raw.includes(':') ? raw.split(':', 1)[0] : raw;
  if (base === 'durationv2' || base === 'duration_v2') return 'duration';
  return base;
}

function normalizePrefixedPath(instr, item) {
  const rawPath = samplePath(item);
  if (!rawPath) return '';
  if (rawPath.startsWith(`/${instr}/`)) return rawPath;
  return `/${instr}${rawPath.startsWith('/') ? '' : '/'}${rawPath}`;
}

function instrumentForPrefix(prefix) {
  const first = String(prefix || '').split('/')[0] || 'composition';
  if (/^\d+$/.test(first)) return 'composition';
  return first;
}

function normalizeInput(parsed) {
  if (parsed && typeof parsed === 'object' && parsed.tracks && !Array.isArray(parsed)) {
    const out = [];
    for (const [instr, arr] of Object.entries(parsed.tracks)) {
      if (!Array.isArray(arr)) continue;
      for (const item of arr) {
        const prefixedPath = normalizePrefixedPath(instr, item);
        if (!prefixedPath) continue;
        out.push({ path: prefixedPath, data: item.data });
      }
    }
    return out;
  }
  if (Array.isArray(parsed)) return parsed;
  throw new Error('Unsupported PT JSON shape.');
}

function convertPTToMIDIEvents(ptResponse) {
  const groups = {};
  ptResponse.forEach((sample) => {
    const rawPath = samplePath(sample);
    const parts = rawPath.split('/').filter(Boolean);
    if (parts.length < 2) return;
    const prefix = parts.slice(0, -1).join('/');
    const scalar = normalizeScalarName(parts.at(-1));
    (groups[prefix] ||= {})[scalar] = sample.data;
  });

  const conductorEvents = [{ type: 'tempo', time: 0, bpm: 120 }];
  const noteBuckets = new Map();

  function pushTimeSig(t, num, den) {
    const last = conductorEvents.at(-1);
    if (!(last && last.type === 'timeSig' && last.time === t && last.numerator === num && last.denominator === den)) {
      conductorEvents.push({ type: 'timeSig', time: t, numerator: num, denominator: den });
    }
  }

  Object.entries(groups).forEach(([_, g]) => {
    if (Array.isArray(g.numerator) && Array.isArray(g.denominator) && Array.isArray(g.time)) {
      g.time.forEach((t, i) => pushTimeSig(Number(t) || 0, g.numerator[i], g.denominator[i]));
    }
  });
  if (!conductorEvents.some((e) => e.type === 'timeSig')) {
    conductorEvents.push({ type: 'timeSig', time: 0, numerator: 4, denominator: 4 });
  }

  let dynamicTrackStart = 0;
  const trackByInstr = new Map();
  const chanByTrack = new Map();
  function ensureTrack(instr) {
    if (trackByInstr.has(instr)) return trackByInstr.get(instr);
    const track = dynamicTrackStart++;
    trackByInstr.set(instr, track);
    chanByTrack.set(track, CHANNELS[track % CHANNELS.length]);
    return track;
  }

  Object.entries(groups).forEach(([prefix, g]) => {
    if (!Array.isArray(g.pitch)) return;
    const instr = instrumentForPrefix(prefix);
    const trackIndex = ensureTrack(instr);
    const channel = chanByTrack.get(trackIndex);

    let tArr = g.time;
    let dArr = g.duration;
    let vArr = g.velocity;
    if (!Array.isArray(tArr)) return;

    const len = Math.min(
      g.pitch.length,
      tArr.length,
      Array.isArray(dArr) ? dArr.length : Infinity,
      Array.isArray(vArr) ? vArr.length : Infinity
    );
    if (len <= 0) return;

    const bucket = noteBuckets.get(instr) || { trackIndex, channel, notes: [] };
    for (let i = 0; i < len; i++) {
      bucket.notes.push({
        midinote: Number(g.pitch[i]),
        time: Number(tArr[i]),
        duration: Array.isArray(dArr) ? Number(dArr[i]) : 1,
        velocity: Array.isArray(vArr) ? Number(vArr[i]) : 80
      });
    }
    noteBuckets.set(instr, bucket);
  });

  return { conductorEvents, noteBuckets };
}

function writeSMF(payload, outPath) {
  const instrumentMeta = payload.instrument_meta || {};
  const instrOrder = deriveInstrOrder(payload);
  const flat = normalizeInput(payload);
  const { conductorEvents, noteBuckets } = convertPTToMIDIEvents(flat);

  const PPQ = 960;
  const smf = JZZ.MIDI.SMF(1, PPQ);
  const conductor = new JZZ.MIDI.SMF.MTrk();
  smf.push(conductor);
  conductor.add(0, JZZ.MIDI.smfSeqName('PT→MIDI (allagma)'));

  let maxTick = 0;
  conductorEvents
    .sort((a, b) => (a.time - b.time) || (a.type === 'tempo' ? -1 : 1))
    .forEach((evt) => {
      const tick = Math.round(PPQ * Math.max(0, Number(evt.time) || 0));
      if (evt.type === 'tempo') conductor.add(tick, JZZ.MIDI.smfBPM(evt.bpm));
      if (evt.type === 'timeSig') conductor.add(tick, JZZ.MIDI.smfTimeSignature(evt.numerator, evt.denominator));
      maxTick = Math.max(maxTick, tick);
    });

  const present = [...noteBuckets.keys()];
  const orderedInstrs = instrOrder.filter((i) => present.includes(i)).concat(present.filter((i) => !instrOrder.includes(i)));

  orderedInstrs.forEach((instrKey, idx) => {
    const bucket = noteBuckets.get(instrKey);
    if (!bucket) return;

    const trk = new JZZ.MIDI.SMF.MTrk();
    smf.push(trk);

    const channel = bucket.channel ?? CHANNELS[idx % CHANNELS.length];
    const meta = metaFor(instrKey, instrumentMeta);
    trk.add(0, JZZ.MIDI.smfSeqName(meta.name));
    trk.add(0, JZZ.MIDI.smfInstrName(meta.name));
    if (meta.bankMSB || meta.bankLSB) {
      trk.add(0, JZZ.MIDI.control(channel, 0, meta.bankMSB));
      trk.add(0, JZZ.MIDI.control(channel, 32, meta.bankLSB));
    }
    trk.add(0, JZZ.MIDI.program(channel, meta.program));

    bucket.notes.forEach((n) => {
      const time = Math.max(0, Number.isFinite(n.time) ? n.time : 0);
      const duration = Math.max(0, Number.isFinite(n.duration) ? n.duration : 0);
      const on = Math.round(PPQ * time);
      const off = Math.max(on + 1, Math.round(PPQ * (time + duration)));
      const vel = Math.max(0, Math.min(127, Math.round(Number.isFinite(n.velocity) ? n.velocity : 80)));
      const pitch = Math.max(0, Math.min(127, Math.round(Number.isFinite(n.midinote) ? n.midinote : 0)));
      trk.add(on, JZZ.MIDI.noteOn(channel, pitch, vel));
      trk.add(off, JZZ.MIDI.noteOff(channel, pitch, 0));
      maxTick = Math.max(maxTick, on, off);
    });

    trk.add(maxTick + 1, JZZ.MIDI.smfEndOfTrack());
  });

  conductor.add(maxTick + 1, JZZ.MIDI.smfEndOfTrack());

  const dumped = smf.dump();
  let buf;
  if (dumped instanceof Uint8Array) buf = Buffer.from(dumped);
  else if (Array.isArray(dumped)) buf = Buffer.from(Uint8Array.from(dumped));
  else if (typeof dumped === 'string') buf = Buffer.from(dumped, 'binary');
  else throw new Error(`Unsupported SMF dump type: ${typeof dumped}`);
  fs.writeFileSync(outPath, buf);
}

const [, , inPath, outPath] = process.argv;
if (!inPath || !outPath) {
  console.error('Usage: node tools/pt2midi.js <input_json> <output_mid>');
  process.exit(2);
}

const payload = JSON.parse(fs.readFileSync(path.resolve(inPath), 'utf8'));
writeSMF(payload, path.resolve(outPath));
console.log('Wrote MIDI:', path.resolve(outPath));
