"""Local WASAPI percussion events. No recordings, microphone or audio uploads.

The detector finds transients, not instruments or musical downbeats. Genre
profiles rank those transients in the client; tempo is an independent estimate.
Dependencies are imported only when capture is requested.
"""
from collections import deque
import re
import queue
import threading
import time
import unicodedata


GENRE_TERMS = {
    "salsa": ("salsa", "timba", "son cubano", "mambo"),
    "bachata": ("bachata",),
    "reggaeton": ("reggaeton", "regueton", "dembow"),
    "merengue": ("merengue",),
    "cumbia": ("cumbia",),
    "electronic": ("house", "techno", "edm", "electro", "dance"),
    "rock": ("rock", "metal", "punk"),
    "pop": ("pop",),
}


def classify_genres(tags):
    """Artist tags are evidence for a suggestion, never proof of track genre."""
    found = set()
    for tag in tags:
        normalized = "".join(c for c in unicodedata.normalize("NFKD", tag.lower())
                             if not unicodedata.combining(c))
        for genre, terms in GENRE_TERMS.items():
            if any(re.search(r"\b" + re.escape(term) + r"\b", normalized) for term in terms):
                found.add(genre)
    # Broad 'pop' labels do not outweigh a more specific dance tradition.
    if len(found) > 1:
        found.discard("pop")
    candidates = sorted(found)
    return {"genre": candidates[0] if len(candidates) == 1 else "mixed" if candidates else "unknown",
            "candidates": candidates, "source": "artist_tags" if candidates else "unknown",
            "confidence": "suggested" if candidates else "unknown"}


class PercussionDetector:
    """Causal, multiband spectral flux with adaptive thresholds and silence gate."""
    def __init__(self, sample_rate, hop=512, active_bands=(0, 1, 2)):
        import numpy as np
        self.np, self.rate, self.hop = np, sample_rate, hop
        self.size = 2048
        self.buffer = np.zeros(self.size)
        self.window = np.hanning(self.size)
        hz = np.fft.rfftfreq(self.size, 1 / sample_rate)
        self.bands = [(hz >= a) & (hz < b) for a, b in ((35, 220), (220, 2500), (2500, 10000))]
        self.active_bands = list(active_bands)
        self.active_mask = np.logical_or.reduce([self.bands[i] for i in self.active_bands])
        self.previous = np.zeros(self.size // 2 + 1)
        self.history = deque(maxlen=max(16, round(1.5 * sample_rate / hop)))
        self.novelty = deque(maxlen=round(8 * sample_rate / hop))
        self.energy = deque(maxlen=round(4 * sample_rate / hop))
        self.last_hit = self.last_drop = -100.0
        self.last_tempo = -100.0
        self.bpm, self.confidence = None, 0.0

    def process(self, samples, at):
        np = self.np
        # Power-preserving channel combination: inverted stereo must not cancel.
        samples = np.asarray(samples, dtype=float)
        if samples.ndim == 2:
            samples = samples[:, np.argmax(np.mean(samples * samples, axis=0))]
        n = len(samples)
        if n != self.hop:
            raise ValueError("Expected one fixed-size audio hop")
        self.buffer[:-n] = self.buffer[n:]
        self.buffer[-n:] = samples
        rms = float(np.sqrt(np.mean(samples * samples)))
        magnitude = np.abs(np.fft.rfft(self.buffer * self.window)) / self.size
        # Native detection ignores midrange even for silence/drop context.
        if self.active_bands != [0, 1, 2]:
            rms = float(np.sqrt(2 * np.sum(magnitude[self.active_mask] ** 2) /
                                np.mean(self.window ** 2)))
        spectrum = np.log1p(30 * magnitude)
        delta = np.maximum(0, spectrum - self.previous)
        self.previous = spectrum
        flux = np.array([float(np.mean(delta[b])) for b in self.bands])
        history = np.array(self.history)
        scores = np.zeros(3)
        if len(history) >= 20:
            median = np.median(history, axis=0)
            mad = np.median(np.abs(history - median), axis=0)
            scores = np.clip((flux - median) / (0.0001 + 3 * mad + median), 0, 12)
        self.history.append(flux)
        self.novelty.append(float(flux[self.active_bands].sum()) if rms > 0.001 else 0.0)
        self.energy.append(rms)
        if rms < 0.001:
            scores[:] = 0
        if at - self.last_tempo >= 0.5:
            self.last_tempo = at
            self._tempo()
        # Pass softer candidates to the visualizer; its genre-weighted threshold
        # decides which ones flash. A higher fixed floor defeats sensitivity UI.
        hit = bool(scores[self.active_bands].max() >= 1.25 and at - self.last_hit >= 0.09)
        drop = False
        if hit:
            self.last_hit = at
            # A sustained lull followed by a low-frequency attack: candidate only.
            e = np.array(self.energy)
            recent = max(1, round(0.7 * self.rate / self.hop))
            if len(e) > recent * 3:
                old, quiet = float(np.mean(e[:-recent])), float(np.mean(e[-recent:-1]))
                drop = bool(old > 0.004 and quiet < old * 0.55 and
                            rms > max(0.008, quiet * 2.5) and scores[0] > 3 and
                            at - self.last_drop > 8)
                if drop:
                    self.last_drop = at
        return {"hit": hit, "at": at, "bands": [round(float(x), 3) for x in scores],
                "level": round(rms, 5), "bpm": self.bpm,
                "tempo_confidence": self.confidence, "drop_candidate": drop}

    def _tempo(self):
        np = self.np
        x = np.array(self.novelty)
        if len(x) < 4 * self.rate / self.hop or float(x.max(initial=0)) < 0.0001:
            self.bpm, self.confidence = None, 0.0
            return
        # Exclude silence/recent stops; never hold a stale BPM indefinitely.
        if max(list(self.energy)[-round(self.rate / self.hop):], default=0) < 0.001:
            self.bpm, self.confidence = None, 0.0
            return
        x -= np.mean(x)
        x = np.convolve(x, [0.25, 0.5, 0.25], mode="same")
        lags = range(round(60 / 220 * self.rate / self.hop), round(60 / 55 * self.rate / self.hop) + 1)
        values = [float(np.dot(x[k:], x[:-k]) /
                        (np.linalg.norm(x[k:]) * np.linalg.norm(x[:-k]) + 1e-12)) for k in lags]
        best = max(values)
        if best < 0.25:
            self.bpm, self.confidence = None, round(max(0, best), 2)
            return
        # Shortest near-equal periodicity avoids repeatedly choosing 60 over 120.
        peaks = [i for i in range(1, len(values)-1)
                 if values[i] >= values[i-1] and values[i] >= values[i+1] and values[i] >= best * 0.9]
        idx = peaks[0] if peaks else int(np.argmax(values))
        lag = float(lags[idx])
        if 0 < idx < len(values)-1:
            a, b, c = values[idx-1:idx+2]
            if abs(a - 2*b + c) > 1e-9:
                lag += float(np.clip(0.5*(a-c)/(a-2*b+c), -0.5, 0.5))
        self.confidence = round(max(0, best), 2)
        self.bpm = round(60 * self.rate / (self.hop * lag), 1)


class LoopbackService:
    """One capture worker shared by SSE clients; releases the device when unused."""
    def __init__(self, active_bands=(0, 1, 2)):
        self.active_bands = active_bands
        self.condition = threading.Condition()
        self.thread = None
        self.clients = 0
        self.sequence = 0
        self.packet = {"state": "idle"}

    def subscribe(self):
        with self.condition:
            self.clients += 1
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._run, daemon=True, name="fiesta-loopback")
                self.thread.start()
            # Do not replay a hit retained from a previous connection.
            return self.sequence

    def unsubscribe(self):
        with self.condition:
            self.clients = max(0, self.clients - 1)

    def wait(self, sequence, timeout=1):
        with self.condition:
            self.condition.wait_for(lambda: self.sequence != sequence, timeout)
            packet = dict(self.packet)
            packet["age_ms"] = max(0, (time.monotonic() - packet.pop("at", time.monotonic())) * 1000)
            packet["sequence"] = self.sequence
            return self.sequence, packet

    def _publish(self, packet):
        with self.condition:
            self.sequence += 1
            self.packet = packet
            self.condition.notify_all()

    def _run(self):
        try:
            import numpy as np
            import pyaudiowpatch as pa
        except ImportError:
            self._publish({"state": "unavailable", "reason": "Instala el soporte de audio con setup_audio.ps1."})
            return
        last_send = 0.0
        while True:
            with self.condition:
                if not self.clients:
                    self.thread = None
                    return
            try:
                with pa.PyAudio() as audio:
                    device = audio.get_default_wasapi_loopback()
                    if not device or not device.get("isLoopbackDevice"):
                        raise RuntimeError("No hay salida WASAPI loopback")
                    rate, channels, hop = int(device["defaultSampleRate"]), int(device["maxInputChannels"]), 512
                    detector = PercussionDetector(rate, hop, self.active_bands)
                    self._publish({"state": "warming", "device": device["name"]})
                    blocks = queue.Queue(maxsize=8)

                    def capture(data, frames, timing, status):
                        # PortAudio timestamps include the hardware/capture delay.
                        age = timing["current_time"] - timing["input_buffer_adc_time"] - frames / rate / 2
                        if not 0 < age < 2:
                            age = device.get("defaultLowInputLatency", 0.02) + frames / rate / 2
                        at = time.monotonic() - age
                        try:
                            blocks.put_nowait((data, at, status))
                        except queue.Full:
                            pass  # Worker also discards old blocks; never build a backlog.
                        return None, pa.paContinue

                    with audio.open(format=pa.paFloat32, channels=channels, rate=rate,
                                    input=True, input_device_index=device["index"], frames_per_buffer=hop,
                                    stream_callback=capture) as stream:
                        check_device = time.monotonic()
                        while True:
                            with self.condition:
                                if not self.clients:
                                    break
                            try:
                                data, at, status = blocks.get(timeout=0.25)
                            except queue.Empty:
                                data = None
                            now = time.monotonic()
                            if data is None:
                                detector = PercussionDetector(rate, hop, self.active_bands)
                                result = {"hit": False, "level": 0, "bpm": None, "tempo_confidence": 0, "at": now}
                            elif now - at > 0.18 or status:
                                detector = PercussionDetector(rate, hop, self.active_bands)
                                continue
                            else:
                                samples = np.frombuffer(data, dtype=np.float32).reshape(-1, channels)
                                result = detector.process(samples, at)
                            if result["hit"] or now - last_send >= 0.25:
                                result.update(state="listening", device=device["name"])
                                self._publish(result)
                                last_send = now
                            if now - check_device > 3:
                                check_device = now
                                if audio.get_default_wasapi_loopback()["index"] != device["index"]:
                                    break
            except Exception as exc:
                self._publish({"state": "unavailable", "reason": "Salida de audio no disponible: " + str(exc)[:160]})
                time.sleep(2)


loopback = LoopbackService()
