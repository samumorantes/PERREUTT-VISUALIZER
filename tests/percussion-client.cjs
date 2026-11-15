const fs = require('fs'), vm = require('vm'), assert = require('node:assert/strict');
const html = fs.readFileSync('index.html', 'utf8');
for (const [, js] of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) new vm.Script(js);
const elements = new Map();
const node = id => {
  if (!elements.has(id)) elements.set(id, {value:'', textContent:'', options:[{},{},{}]});
  return elements.get(id);
};
let now = 1000, calibration = {genre:'auto',offset:0};
const flashes = [];
const context = vm.createContext({
  $, performance:{now:() => now}, localStorage:{getItem:()=>null,setItem(){}},
  document:{hidden:false,addEventListener(){}}, addEventListener(){}, setInterval(){},
  setTimeout, clearTimeout, AbortController, console,
  curTrack:'one', S:{track:{id:'one'}}, playing:true, lyricsFrozen:false,
  rhythmEpoch:0, rhythmUIKey:'', partyFlash:null, cfg:{timing:'beats',dropFx:true},
  REDUCED_MOTION:{matches:false}, TRANSLATION_DISPLAY:false,
  rhythmCalibration:()=>calibration, saveRhythmSettings:v=>{calibration=v;},
  isChill:()=>false, fluidPulse(){}, explodeDrop(){},
  onColor:(age,interval)=>flashes.push({age,interval}),
  EventSource:class {close(){this.closed=true;}},
});
function $(id) { return node(id); }
vm.runInContext(html.slice(html.indexOf('const GENRE_PROFILES ='), html.indexOf('function rhythmEvents()')), context);
const run = js => vm.runInContext(js, context);
run('maintainPercussion(); renderLivePercussion()');
now += 250;
let sequence = 0;
function hit(extra={}) {
  context.inputPacket = {state:'listening', device:'test', hit:true, sequence:++sequence,
    age_ms:20, bands:[6,4,1], bpm:120, tempo_confidence:.9, level:.1, ...extra};
  run('liveAudio.stream.onmessage({data:JSON.stringify(inputPacket)})');
}
hit(); run('renderLivePercussion()'); assert.equal(flashes.length,1);
assert.equal(flashes[0].age,.02);
// Moderate transients that previously flashed now stay below the higher threshold.
now += 250; hit({bands:[3.8,1,1]}); run('renderLivePercussion()'); assert.equal(flashes.length,1);
now += 250; hit({age_ms:500}); run('renderLivePercussion()'); assert.equal(flashes.length,1);
// Duplicate sequence is never replayed.
hit({sequence:sequence}); run('renderLivePercussion()'); assert.equal(flashes.length,1);
// Silence and device failure suppress grid fallback.
assert.equal(run('renderLivePercussion()'),true);
context.playing=false; now+=250; hit(); run('renderLivePercussion()'); assert.equal(flashes.length,1);
context.playing=true; now+=250;
calibration={genre:'bachata',offset:-150};
hit(); run('renderLivePercussion()'); assert.equal(flashes.length,1);
now+=140; run('renderLivePercussion()'); assert.equal(flashes.length,2);
// Seeking invalidates a queued delayed event.
now+=250; hit(); context.rhythmEpoch++; run('renderLivePercussion()');
now+=250; run('renderLivePercussion()'); assert.equal(flashes.length,2);
// Positive map offsets cannot anticipate live audio, nor discard every hit.
calibration={genre:'auto',offset:500}; hit(); run('renderLivePercussion()'); assert.equal(flashes.length,3);
// Long stalled frames discard queued attacks instead of bursting.
now+=250; hit(); now+=1000; run('renderLivePercussion()'); assert.equal(flashes.length,3);
// Reduced motion and hidden tabs discard pending attacks.
hit(); context.REDUCED_MOTION.matches=true; run('renderLivePercussion()'); assert.equal(flashes.length,3);
context.REDUCED_MOTION.matches=false; context.document.hidden=true;
now+=250; hit(); run('renderLivePercussion()'); assert.equal(flashes.length,3);
// Strong-accent mode also rejects moderate hits and still accepts strong ones.
context.document.hidden=false; context.cfg.timing='bars';
run('renderLivePercussion()'); now+=250;
hit(); run('renderLivePercussion()'); assert.equal(flashes.length,3);
now+=250; hit({bands:[9,4,1]}); run('renderLivePercussion()'); assert.equal(flashes.length,4);
// Explicit map mode returns control to the existing scheduler.
run('audioInput="grid"'); assert.equal(run('renderLivePercussion()'),false);
console.log('PASS: inline syntax, higher onset threshold, event phase, duplicates, stale events, pause, offset, seek, silence, reduced motion, map fallback');
