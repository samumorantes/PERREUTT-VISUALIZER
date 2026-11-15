// Local, pinned shaders.com MIT library. No CDN, account or telemetry required.
import { createShader, setShadersDebug } from 'shaders/js';
setShadersDebug(new URLSearchParams(location.search).has('debugEffects'));

const node = (type, id, props = {}, children = []) => ({ type, id, props, children });
const backgrounds = { flow: 'FlowingGradient', swirl: 'Swirl', plasma: 'Plasma', aurora: 'Aurora' };
const transitionTypes = { tv: 'RandomBars', shutter: 'BarnDoors', flashcolor: 'NoiseDissolve' };
const slots = Object.fromEntries(['fluid', 'crt', 'transition'].map(name => [name, {
  canvas: document.getElementById(`shader-${name}`), instance: null,
  key: '', pending: false, ready: false, failed: false, running: true, size: '',
}]));
const supported = !!navigator.gpu && isSecureContext && !new URLSearchParams(location.search).has('legacyEffects');
let disposed = false, lastUpdate = -Infinity, lastState = null, transition = null;

function fail(slot, reason) {
  slot.ready = false;
  slot.failed = true;
  slot.reason = reason;
  slot.canvas.style.opacity = '0';
  slot.instance?.destroy();
}

async function ensure(slot, key, components) {
  if (!supported || disposed || slot.failed || slot.pending || slot.key === key) return;
  slot.pending = true;
  slot.ready = false;
  slot.key = key;
  slot.size = '';
  slot.configKey = '';
  slot.paletteKey = '';
  slot.instance?.destroy();
  slot.instance = null;
  slot.running = true;
  try {
    const instance = await createShader(slot.canvas, { components }, {
      disableTelemetry: true, observeElement: false, colorSpace: 'srgb',
      onReady: () => { if (!disposed && !slot.failed) slot.ready = true; },
      onError: reason => fail(slot, reason),
    });
    if (disposed) instance.destroy();
    else {
      slot.instance = instance;
      if (instance.getFailureReason()) fail(slot, instance.getFailureReason());
      else if (slot.failed) instance.destroy();
    }
  } catch (error) {
    fail(slot, String(error));
  } finally {
    slot.pending = false;
  }
}

function running(slot, enabled) {
  if (!slot.instance || !slot.ready || slot.failed || slot.running === enabled) return;
  slot.running = enabled;
  if (enabled) slot.instance.resume(); else slot.instance.pause();
}

function resize(slot, state, fine = false) {
  if (!slot.instance || !slot.ready) return;
  // Render the fluid at reduced resolution; keep phosphors sharp on the GPU.
  const scale = fine ? (state.quality > 1 ? 1 : 0.75) : (state.quality > 1 ? 0.65 : 0.4);
  const w = Math.max(2, Math.round(state.width * scale));
  const h = Math.max(2, Math.round(state.height * scale));
  const key = `${w}x${h}`;
  if (slot.size === key) return;
  slot.size = key;
  slot.instance.resize(w, h);
  // resize() also sets CSS pixels; preserve the crystal's layout dimensions.
  slot.canvas.style.width = slot.canvas.style.height = '100%';
}

function palette(state) {
  const cols = state.palette?.length ? state.palette : [[78, 31, 154], [23, 155, 180], [231, 74, 145], [254, 170, 90]];
  return Array.from({ length: 4 }, (_, i) => '#' + cols[i % cols.length]
    .map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join(''));
}

function fluidTree(type, trails) {
  // Aurora is translucent: give every composition its own opaque backdrop
  // instead of exposing the last party-mode flash through its empty regions.
  const source = node('Group', 'scene', {}, [
    node('SolidColor', 'fluid-base', { color: '#090b20' }),
    node(type, 'fluid', { speed: 0.3 }),
  ]);
  return trails ? [node('TimeTrail', 'trails', {
    trailLength: 0.45, diffusion: 0.35, trailOpacity: 0.25, trailBlend: 'screen',
  }, [source])] : [source];
}

function crtTree() {
  // A white shader texture multiplied over the DOM textures the lyrics and UI
  // without taking experimental HTML screenshots or rasterizing their text.
  // No Vignette node here: its box-like contours drew a straight dark edge
  // inside the curved tube. The CSS ellipse (#vignette) follows the glass.
  return [node('SolidColor', 'base-white', { color: '#ffffff' }),
    node('FilmGrain', 'grain', { bias: 0, strength: 0.06, animated: true }, [
      node('CRTScreen', 'crt', { pixelSize: 128, colorShift: 0, vignetteIntensity: 0 }, [
        node('SolidColor', 'white', { color: '#ffffff' }),
      ]),
    ])];
}

function transitionTree(mode) {
  const fill = mode === 'shutter'
    ? node('SolidColor', 'fill', { color: '#08080c' })
    : mode === 'tv'
      ? node('FilmGrain', 'static', { strength: 0.9, bias: 0, animated: true }, [node('SolidColor', 'fill', { color: '#8a8a8a' })])
      : node('FlowingGradient', 'fill', { speed: 0.3 });
  return [node(transitionTypes[mode], 'wipe', { progress: 1, feather: 0.03, softness: 0.16, barCount: 24 }, [fill])];
}

function tick(now, state) {
  if (disposed) return;
  lastState = state;
  const { cfg, quality, reduced, egg } = state;
  const active = supported && !document.hidden && !egg && quality > 0;
  const f = slots.fluid, c = slots.crt, tr = slots.transition;
  const type = backgrounds[cfg.fluidStyle] || backgrounds.flow;
  const trails = cfg.trails && quality >= 2 && !reduced;
  if (active) {
    if (state.chill) void ensure(f, `${type}:${trails}`, fluidTree(type, trails));
    void ensure(c, 'crt', crtTree());
    if (transitionTypes[cfg.transition] && !reduced) void ensure(tr, cfg.transition, transitionTree(cfg.transition));
  }
  const fluidOn = active && state.chill && f.ready && !f.failed && f.key === `${type}:${trails}`;
  const crtOn = active && c.ready && !c.failed;
  api.fluidActive = fluidOn;
  document.body.classList.toggle('shader-fluid', fluidOn);
  document.body.classList.toggle('shader-crt', crtOn);
  f.canvas.style.opacity = fluidOn ? '1' : '0';
  c.canvas.style.opacity = crtOn ? '1' : '0';
  running(f, fluidOn);
  running(c, crtOn);
  running(tr, active && !!transition);
  if (!active) { cancelTransition(); return; }

  if (now - lastUpdate >= 33) {
    lastUpdate = now;
    const cols = palette(state);
    if (fluidOn) {
      resize(f, state);
      const pkey = cols.join();
      if (pkey !== f.paletteKey) {
        f.paletteKey = pkey;
        f.instance.update('fluid', { colorA: cols[0], colorB: cols[1], colorC: cols[2], colorD: cols[3],
          stops: cols.map((color, i) => ({ color, position: i / (cols.length - 1) })) });
      }
      const energy = reduced ? 0 : Math.min(2.6, state.energy);
      const speed = reduced ? 0 : Math.max(0.1, Math.min(1, state.tempo / 240));
      const props = { speed };
      if (type === 'FlowingGradient') props.distortion = 0.45 + energy * 0.3;
      if (type === 'Swirl') props.detail = 1.1 + energy * 0.25;
      if (type === 'Plasma') { props.warp = 0.35 + energy * 0.12; props.intensity = 1.1 + energy * 0.25; }
      if (type === 'Aurora') { props.intensity = 65 + energy * 10; props.waviness = 35 + energy * 12; props.curtainCount = quality >= 2 ? 3 : 1; }
      f.instance.update('fluid', props);
    }
    if (crtOn) {
      resize(c, state, true);
      const key = [cfg.scanOn, cfg.scan, cfg.mask, cfg.noise, reduced, state.height].join();
      if (key !== c.configKey) {
        c.configKey = key;
        c.instance.update('crt', { scanlineIntensity: cfg.scanOn ? cfg.scan / 100 * 0.35 : 0,
          scanlineFrequency: Math.max(100, Math.min(800, state.height / 2)),
          // Fade the phosphor mask independently from the scanline switch.
          opacity: cfg.scanOn ? Math.max(cfg.mask / 100 * 0.45, cfg.scan / 100 * 0.35) : 0 });
        c.instance.update('grain', { strength: cfg.noise / 100 * 0.16, animated: !reduced });
      }
    }
  }
  if (transition && tr.ready && !tr.failed) {
    resize(tr, state);
    const progress = Math.min(1, (now - transition.start) / transition.duration);
    tr.instance.update('wipe', { progress: transition.mode === 'shutter' ? Math.abs(progress * 2 - 1) : progress });
    if (progress >= 1) cancelTransition();
  }
}

function playTransition(mode) {
  const slot = slots.transition;
  if (!lastState || lastState.reduced || lastState.egg || lastState.quality === 0 ||
      !slot.ready || slot.failed || slot.key !== mode || !transitionTypes[mode]) return false;
  const cols = palette(lastState);
  if (mode === 'flashcolor') slot.instance.update('fill', { colorA: cols[0], colorB: cols[1], colorC: cols[2], colorD: cols[3] });
  transition = { mode, start: performance.now(), duration: mode === 'shutter' ? 1100 : 800 };
  slot.instance.update('wipe', { progress: mode === 'shutter' ? 1 : 0 });
  slot.canvas.style.opacity = '1';
  running(slot, true);
  return true;
}

function cancelTransition() {
  transition = null;
  slots.transition.canvas.style.opacity = '0';
  running(slots.transition, false);
}

function dispose() {
  disposed = true;
  Object.values(slots).forEach(slot => slot.instance?.destroy());
}

const api = window.FiestaShaders = {
  tick, playTransition, cancelTransition, fluidActive: false,
  status: () => ({ supported, fluidActive: api.fluidActive, transition: transition?.mode || null,
    layers: Object.fromEntries(Object.entries(slots).map(([name, slot]) => [name, {
      key: slot.key, ready: slot.ready, failed: slot.failed, reason: slot.reason || null, size: slot.size, running: slot.running,
    }])) }),
};
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { Object.values(slots).forEach(slot => running(slot, false)); cancelTransition(); }
});
window.addEventListener('pagehide', event => { if (!event.persisted) dispose(); });
