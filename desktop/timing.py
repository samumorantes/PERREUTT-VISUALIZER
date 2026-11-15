"""Renderer-independent playback clock and pulse scheduling."""
import bisect
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


class PulseScheduler:
    def __init__(self):
        self.queue = []
        self.sequence = -1
        self.last_hit = -math.inf
        self.ready_at = 0
        self.context_at = 0

    def reset(self, now):
        self.queue.clear()
        self.ready_at = now + .18
        self.context_at = now
        self.last_hit = -math.inf

    def ingest(self, packet, now, genre="unknown", threshold=1.75, offset=0, mode="beats"):
        seq = packet.get("sequence", -1)
        if seq <= self.sequence:
            return
        self.sequence = seq
        age = packet.get("age_ms", 1e6) / 1000 + max(0, now - packet.get("received_at", now))
        if not packet.get("hit") or age > .18 or now < self.ready_at:
            return
        bands = packet.get("bands", [])
        if len(bands) != 3 or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in bands):
            return
        weights = PROFILES.get(genre, PROFILES["unknown"])[1]
        score = max(x*w for x, w in zip(bands, weights))
        if score < threshold or now - self.last_hit < .12:
            return
        self.last_hit = now
        drop = bool(packet.get("drop_candidate")) and now-self.context_at >= 8
        if mode == "bars" and score < threshold + 3 or mode == "sections" and not drop:
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
