"""Renderer-independent playback clock and pulse scheduling."""
import bisect
from collections import deque
import math
import time


PALETTE = ("#ff1744", "#ff6d00", "#ffd600", "#00e676", "#00b0ff", "#651fff", "#d500f9")
PROFILES = {
    "auto": ("Automático", (1, 1, .65)),
    "unknown": ("Sin clasificar", (1, 1, .65)),
    "mixed": ("Mixto / otro", (1, 1, .65)),
    "salsa": ("Salsa", (.75, 1.2, .8)),
    "bachata": ("Bachata", (.9, 1.1, .65)),
    "reggaeton": ("Reguetón", (1.2, 1, .45)),
    "merengue": ("Merengue", (.9, 1.1, .7)),
    "cumbia": ("Cumbia", (1, 1, .7)),
    "electronic": ("Electrónica", (1.2, 1, .5)),
    "pop": ("Pop", (1, 1, .6)),
    "rock": ("Rock", (1.1, 1, .55)),
}


class PlaybackClock:
    def __init__(self, now=time.monotonic):
        self.now = now
        self.position = 0.0
        self.at = now()
        self.playing = False
        self.correction = 0.0
        self.track = None

    def read(self):
        elapsed = max(0, self.now() - self.at)
        return self.position + (elapsed if self.playing else 0) + self.correction * min(1, elapsed / .6)

    def update(self, position, playing, track):
        current = self.read()
        reset = track != self.track or playing != self.playing or abs(position-current) > .2
        self.position = float(position) if reset or not playing else current
        self.correction = 0 if reset or not playing else float(position)-current
        self.playing, self.track, self.at = bool(playing), track, self.now()
        return reset


class AdaptiveThreshold:
    """Learn transient clutter, not raw loudness, from ALL fresh candidates.

    Spectral flux is already normalized by the audio detector. A six-second
    window of candidate strengths/density distinguishes a busy background from
    isolated strong percussion. No beat grid, BPM or accepted-flash feedback is
    used. An isolated loud attack cannot move the gate by itself.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.events = deque(maxlen=100)
        self.started = self.updated = self.quiet_since = None
        self.extra = 0.0
        self.learning = True

    def update(self, now, score=None, level=None):
        if self.started is None:
            self.started = now
        dt = min(.5, max(0., now-self.updated)) if self.updated is not None else 0.
        self.updated = now
        if level is not None and level < .001:
            if self.quiet_since is None:
                self.quiet_since = now
            if now-self.quiet_since >= .75:
                self.reset()
                return
        else:
            self.quiet_since = None
        if score is not None:
            self.events.append((now,score))
        while self.events and self.events[0][0] < now-6.:
            self.events.popleft()
        elapsed = now-self.started
        self.learning = elapsed < 2.
        target = 0.
        if not self.learning and len(self.events) >= 6:
            scores = sorted(score for _,score in self.events)
            # Lower quantile represents weaker, recurring attacks. Strong beats
            # and occasional drops must not dominate the background estimate.
            background = scores[int((len(scores)-1)*.4)]
            strong = scores[int((len(scores)-1)*.9)]
            density = len(scores)/min(6.,elapsed)
            busy = max(0.,min(1.,(density-2.5)/2.5))
            # A fast, even drum pattern is not evidence of noise. Only separate
            # weak activity when stronger attacks actually stand above it.
            separation = max(0.,min(1.,strong-background))
            # 1.25 is the detector's candidate floor. Keep the user's base as an
            # additive sensitivity bias instead of replacing it with a percentile.
            target = min(8.,max(0.,background-1.25))*busy*separation
        # Smooth increases; recover more slowly to avoid fluttering thresholds.
        tau = 1.2 if target > self.extra else 3.
        self.extra += (target-self.extra)*(1-math.exp(-dt/tau))

    def threshold(self, base):
        return min(12.,base+self.extra)


class PulseScheduler:
    def __init__(self):
        self.queue = []
        self.sequence = -1
        self.last_hit = -math.inf
        self.ready_at = 0
        self.context_at = 0
        self.adaptation = AdaptiveThreshold()
        self.effective_threshold = 1.75

    def reset(self, now, reset_adaptation=True):
        self.queue.clear()
        self.ready_at = now + .18
        self.context_at = now
        self.last_hit = -math.inf
        if reset_adaptation:
            self.adaptation.reset()

    def ingest(self, packet, now, genre="unknown", threshold=1.75, offset=0, mode="beats", adaptive=True,
               bass_gain=1., treble_gain=1.):
        seq = packet.get("sequence", -1)
        if seq <= self.sequence:
            return
        self.sequence = seq
        age = packet.get("age_ms", 1e6) / 1000 + max(0, now - packet.get("received_at", now))
        if not math.isfinite(age) or age < 0 or age > .18 or now < self.ready_at:
            return
        level = packet.get("level")
        if level is not None and (not isinstance(level,(int,float)) or not math.isfinite(level)):
            return
        bands = packet.get("bands", [])
        if len(bands) != 3 or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in bands):
            if level is not None and level < .001 and not packet.get("hit"):
                self.adaptation.update(now,level=level)
            return
        weights = PROFILES.get(genre, PROFILES["unknown"])[1]
        # Midrange is never eligible, irrespective of the genre profile.
        score = max(bands[0]*weights[0]*bass_gain, bands[2]*weights[2]*treble_gain)
        audible = level is None or level >= .001
        self.adaptation.update(now, score if packet.get("hit") and audible and score > 0 else None, level)
        self.effective_threshold = self.adaptation.threshold(threshold) if adaptive else threshold
        if not packet.get("hit") or not audible or score < self.effective_threshold or now - self.last_hit < .12:
            return
        self.last_hit = now
        drop = bool(packet.get("drop_candidate")) and bass_gain > 0 and now-self.context_at >= 8
        if mode == "bars" and score < self.effective_threshold + 3 or mode == "sections" and not drop:
            return
        bpm = packet.get("bpm") if now-self.context_at >= 8 else None
        duration = .94 * (60 / bpm if bpm and 30 <= bpm <= 260 else .5)
        self.queue.append({"at": now-age-min(0, offset/1000), "duration": duration,
                           "color": PALETTE[seq % len(PALETTE)], "drop": drop})
        self.queue = self.queue[-8:]

    def due(self, now):
        due = [p for p in self.queue if p["at"] <= now]
        self.queue = [p for p in self.queue if p["at"] > now]
        if not due or now-due[-1]["at"] > .2:
            return None
        pulse = dict(due[-1])
        pulse["age"] = now-pulse["at"]
        return pulse


def active_line(lines, position):
    return bisect.bisect_right([line["t"] for line in lines], position) - 1


def word_groups(tokens):
    """Keep syllable groups together when the native Flow wraps a phrase."""
    groups = []
    for token in tokens or []:
        if not isinstance(token, dict) or not token.get("text"):
            continue
        if not groups or not token.get("part"):
            groups.append({"text": "", "syllables": []})
        group = groups[-1]
        group["text"] += str(token["text"])
        start = float(token.get("t", 0))
        group["syllables"].append({"text": str(token["text"]), "t": start,
                                   "end": max(start+.01, float(token.get("end") or start+.3))})
    return groups
