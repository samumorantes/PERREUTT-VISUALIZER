"""Native UI bridge. All network/audio work stays outside the GUI thread."""
import bisect
import base64
from collections import Counter
import copy
import html
import json
import math
from pathlib import Path
import queue
import re
import random
import threading
import time
import urllib.parse

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot, QUrl, QBuffer, QIODevice
from PySide6.QtGui import QDesktopServices, QImage, QColor, QGuiApplication

import server as backend
from percussion import classify_genres, loopback
from desktop.timing import PlaybackClock, PulseScheduler, PALETTE, PROFILES, active_line, word_groups


from desktop.preferences import (DEFAULTS, RANGES, ENUMS, THEMES, PALETTES, DARK_DEEP, GENRE_VISUAL_PRESETS,
                                 PRESET_KEYS, clean_setting, validate, preset_keys, find_preset, is_special, egg_kind, random_palette)


class Controller(QObject):
    viewChanged = Signal()
    lyricChanged = Signal()
    settingsChanged = Signal()
    positionChanged = Signal()
    pulse = Signal(float, float, str, bool)
    clearPulse = Signal()
    openSecond = Signal()
    transitionRequested = Signal(str)
    dropRequested = Signal()
    presetsChanged = Signal()
    incoming = Signal(object)

    def __init__(self, data_dir, smoke=False):
        super().__init__()
        self.smoke = smoke
        self.path = Path(data_dir) / "desktop-settings.json"
        self._settings = copy.deepcopy(DEFAULTS)
        self.track_settings = {}
        self.presets_store = {}
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            for key, value in saved.get("settings", {}).items():
                cleaned = self.clean_setting(key, value)
                if cleaned is not None:
                    self._settings[key] = cleaned
            self.track_settings = saved.get("tracks", {})
            for key, value in (saved.get("presets", {}) or {}).items():
                if isinstance(key, str) and key.startswith(("song:","artist:","album:")):
                    self.presets_store[key] = {k:v for k,v in validate(value).items() if k in PRESET_KEYS}
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        if not isinstance(self.track_settings, dict):
            self.track_settings = {}
        self.base_settings = copy.deepcopy(self._settings)
        self.active_preset = ""
        self.cover_palette = list(DEFAULTS["customPalCols"])
        self.special_track = False
        self.raw_lyrics = []
        self.color_cursor = 0
        self.section_cursor = -1
        self.loaded_track = None
        self.loading_track = False
        self.signed_out = False
        self.logout_pending = False
        self._view = dict(title="FIESTA", artist="Aplicación nativa · Direct3D", cover="", playing=False,
                          status="Conectando con Spotify…", genre="Sin clasificar", genreKey="auto",
                          genreOrigin="", audio="Esperando reproducción", duration=0.0, chill=False,
                          queue="", offset=0.0, bpm=0.0, demo=False, message="", loggedIn=False,
                          palette=self.cover_palette, preset="", qrImage="", qrUrl="", qualityScale=1.0,
                          performance="", lyricSource="", special=False)
        self._lyric = dict(text="FIESTA", back="", groups=[], translated="", translationStatus="", title=True, egg="", start=0.0)
        self._position = 0.0
        self.clock = PlaybackClock()
        self.scheduler = PulseScheduler()
        self.state = {}
        self.line_index = -99
        self.line_key = None
        self.grid_cursor = -1
        self.last_position_emit = 0
        self.taps = []
        self.translation_active = False
        self.translation_cache = {}
        self.translation_pending = set()
        self.evidence = {"genre": "unknown", "source": "unknown"}
        self.stop = threading.Event()
        self.want_audio = threading.Event()
        self.jobs = queue.Queue(maxsize=16)
        self.windows_active = True
        self.incoming.connect(self.receive)
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        if smoke:
            self._settings.update(mood="chill", source="grid")
            self.base_settings.update(mood="chill", source="grid")
            self.receive({"kind": "state", "data": self.smoke_state(), "received_at": time.monotonic()})
        else:
            for target in (self.playback_worker, self.audio_worker, self.job_worker):
                threading.Thread(target=target, daemon=True).start()

    clean_setting = staticmethod(clean_setting)

    @Property("QVariantMap", notify=viewChanged)
    def view(self):
        return self._view

    @Property("QVariantMap", notify=lyricChanged)
    def lyric(self):
        return self._lyric

    @Property("QVariantMap", notify=settingsChanged)
    def settings(self):
        return self._settings

    @Property("QVariantList", notify=presetsChanged)
    def presets(self):
        return [{"key": k, "label": k, "active": k == self.active_preset}
                for k in sorted(self.presets_store)]

    @Property(str, notify=presetsChanged)
    def presetSummary(self):
        return json.dumps(self.presets_store, ensure_ascii=False, indent=2)

    @Property("QVariantList", notify=settingsChanged)
    def genreStyles(self):
        return [dict(key=key, name=recipe["name"], description=recipe["description"],
                     colors=recipe["settings"]["customPalCols"] if recipe["settings"]["mood"] == "chill"
                     else PALETTES[recipe["settings"]["palette"]][:5],
                     active=all(self._settings.get(k) == v for k,v in recipe["settings"].items()))
                for key,recipe in GENRE_VISUAL_PRESETS.items()]

    @Slot(str)
    def applyGenreStyle(self, key):
        recipe = GENRE_VISUAL_PRESETS.get(key)
        if recipe is None:
            return
        values = copy.deepcopy(recipe["settings"])
        self.base_settings.update(values)
        self._settings.update(copy.deepcopy(values))
        self.active_preset = ""
        self.special_track = False
        self.clearPulse.emit()
        self.settingsChanged.emit()
        self.presetsChanged.emit()
        self.refresh_profile()
        self.set_view(message="Estilo aplicado: " + recipe["name"])
        self.save_timer.start(300)

    @Property(float, notify=positionChanged)
    def position(self):
        return self._position

    def set_view(self, **values):
        if any(self._view.get(k) != v for k, v in values.items()):
            self._view.update(values)
            self.viewChanged.emit()

    def calibration(self):
        value = self.track_settings.get(self.clock.track, {})
        if not isinstance(value, dict):
            return {}
        clean = {"genre": value.get("genre", "auto") if value.get("genre", "auto") in PROFILES else "auto"}
        for key, low, high in (("offset", -500, 500), ("bpm", 40, 240), ("anchor", -3600, 86400)):
            v = value.get(key)
            if isinstance(v, (int, float)) and math.isfinite(v) and low <= v <= high:
                clean[key] = v
        return clean

    def genre(self):
        chosen = self.calibration().get("genre", "auto")
        return chosen if chosen in PROFILES and chosen != "auto" else self.evidence.get("genre", "unknown")

    @Slot(str, "QVariant")
    def setSetting(self, key, value):
        if key in ("genre", "offset"):
            if not self.clock.track:
                return
            c = dict(self.calibration())
            if key == "genre":
                if value not in PROFILES:
                    return
                c[key] = value
            else:
                try:
                    c[key] = max(-500, min(500, float(value)))
                except (TypeError, ValueError):
                    return
            self.track_settings[self.clock.track] = c
        else:
            value = self.clean_setting(key, value)
            if value is None:
                return
            self._settings[key] = value
            self.base_settings[key] = copy.deepcopy(value)
            if key == "theme":
                self._settings.update(THEMES[value])
                self.base_settings.update(THEMES[value])
            if key == "globalLock":
                self.apply_music_preset()
        self.settingsChanged.emit()
        self.scheduler.reset(time.monotonic())
        self.grid_cursor = -1
        self.clearPulse.emit()
        self.refresh_profile()
        if key in ("fromLang", "toLang", "upper", "easterEggs", "phrase"):
            self.line_key = None
        if key == "phrase":
            self.rephrase()
        if key == "qrEnabled" and value:
            self.prepareQR()
        self.save_timer.start(300)

    def refresh_profile(self):
        c = self.calibration()
        manual = c.get("genre", "auto") != "auto"
        label = PROFILES.get(self.genre(), PROFILES["unknown"])[0]
        s = self._settings
        palette = s["customPalCols"] if s["customPal"] else DARK_DEEP if self.special_track else self.cover_palette
        self.set_view(genre=label, genreKey=c.get("genre", "auto"), offset=c.get("offset", 0),
                      genreOrigin="Elegido por ti" if manual else "Sugerencia por artista" if self.evidence.get("source") == "artist_tags" else "Sin etiquetas suficientes",
                      palette=list(palette), preset=self.active_preset, special=self.special_track,
                      chill=s["palette"] != "byn" and (s["mood"] == "chill" or
                      s["mood"] == "auto" and (self.special_track or s["autoMood"] and self.state.get("mood") == "chill")))

    @Slot()
    def save(self):
        if self.smoke:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tracks = dict(list(self.track_settings.items())[-200:])
            tmp.write_text(json.dumps({"settings": self.base_settings, "tracks": tracks,
                                      "presets": self.presets_store}, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            self.set_view(message="No se pudieron guardar los ajustes.")

    def rephrase(self):
        duration = self._view.get("duration", 0)
        self.state["lyrics"] = backend.split_phrases(copy.deepcopy(self.raw_lyrics), duration, int(self._settings["phrase"]))
        self.line_key = None

    def apply_music_preset(self):
        track = self.state.get("track") or {}
        self._settings = copy.deepcopy(self.base_settings)
        self.active_preset = ""
        self.special_track = False
        if not self.base_settings["globalLock"]:
            if is_special(track):
                self._settings.update(THEMES["vaporwave"], theme="vaporwave")
                self.special_track = True
            found = find_preset(self.presets_store, track)
            if found:
                self.active_preset, preset = found
                self._settings.update({k:v for k,v in preset.items() if k in PRESET_KEYS})
        self.settingsChanged.emit()
        self.presetsChanged.emit()
        self.rephrase()
        self.refresh_profile()
        if self._settings['qrEnabled']:
            self.prepareQR()

    @Slot(str)
    def savePreset(self, kind):
        track = self.state.get("track") or {}
        key = preset_keys(track).get(kind)
        if not key or kind == "album" and not track.get("album"):
            self.set_view(message="No hay datos de esa canción, artista o álbum todavía.")
            return
        self.presets_store[key] = {k:copy.deepcopy(v) for k,v in self._settings.items() if k in PRESET_KEYS}
        self.set_view(message="Preset guardado: " + kind)
        self.apply_music_preset()
        self.save_timer.start(300)

    @Slot(str)
    def deletePreset(self, key):
        self.presets_store.pop(key, None)
        self.apply_music_preset()
        self.save_timer.start(300)

    @Slot()
    def clearPresets(self):
        self.presets_store.clear()
        self.apply_music_preset()
        self.set_view(message="Presets borrados; configuración habitual restaurada.")
        self.save_timer.start(300)

    @Slot()
    def copyPresets(self):
        QGuiApplication.clipboard().setText(self.presetSummary)
        self.set_view(message="Presets copiados al portapapeles.")

    @Slot(str)
    def importPresets(self, text):
        try:
            if len(text) > 2_000_000:
                raise ValueError()
            store = json.loads(text)
            if not isinstance(store, dict) or len(store) > 1000:
                raise ValueError()
            parsed = {}
            for key,value in store.items():
                if not isinstance(key,str) or not key.startswith(("song:","artist:","album:")) or not isinstance(value,dict):
                    raise ValueError()
                parsed[key] = {k:v for k,v in validate(value,web=True).items() if k in PRESET_KEYS}
            self.presets_store.update(parsed)
            self.apply_music_preset()
            self.save_timer.start(300)
            self.set_view(message=f"Importados {len(parsed)} presets.")
        except (ValueError, TypeError):
            self.set_view(message="JSON de presets no válido. No se ha importado nada.")

    @Slot()
    def resetSettings(self):
        self.base_settings = copy.deepcopy(DEFAULTS)
        self._settings = copy.deepcopy(DEFAULTS)
        self.active_preset = ""
        self.special_track = False
        self.settingsChanged.emit()
        self.presetsChanged.emit()
        self.rephrase()
        self.refresh_profile()
        self.clearPulse.emit()
        self.set_view(message="Configuración restablecida. Tus presets se conservan.")
        self.save_timer.start(300)

    @Slot()
    def toggleCrt(self):
        keys = ("scanOn","flicker","tilt","refresh","fish")
        target = not all(self._settings[k] for k in keys)
        for key in keys:
            self._settings[key] = self.base_settings[key] = target
        for key in ("scan","mask","vignette","grain"):
            self._settings[key] = self.base_settings[key] = (self._settings[key] or 60) if target else 0
        self.settingsChanged.emit()
        self.save_timer.start(300)

    @Slot(int, str)
    def setPaletteColor(self, index, color):
        colors = list(self._settings["customPalCols"])
        if not 0 <= index < len(colors) or not re.fullmatch(r"#[0-9a-fA-F]{6}",color):
            self.set_view(message="Escribe un color hexadecimal como #5a2a91.")
            return
        colors[index] = color
        self.setSetting("customPalCols",colors)

    @Slot()
    def randomPalette(self):
        self.setSetting("customPalCols",random_palette(random))

    @Slot()
    def testTransition(self):
        if not self._settings["reducedMotion"]:
            self.transitionRequested.emit(self._settings["transition"])

    @Slot()
    def testDrop(self):
        if not self._settings["reducedMotion"] and self._settings["dropFx"]:
            self.dropRequested.emit()

    @Slot(float)
    def reportFps(self, fps):
        # Called once a second by the primary visible window, never per frame.
        if not self._settings["autoQuality"]:
            self.bad_frames = self.good_frames = 0
            self.set_view(qualityScale=1.0, performance=f"{fps:.0f} FPS · calidad manual")
            return
        self.bad_frames = getattr(self,"bad_frames",0)+1 if fps < 45 else 0
        self.good_frames = getattr(self,"good_frames",0)+1 if fps > 55 else 0
        scale = self._view["qualityScale"]
        if self.bad_frames >= 2:
            scale = max(.55,scale-.15); self.bad_frames = 0
        if self.good_frames >= 10:
            scale = min(1.,scale+.15); self.good_frames = 0
        self.set_view(qualityScale=scale,performance=f"{fps:.0f} FPS · efectos {round(scale*100)}%")

    @Slot()
    def prepareQR(self):
        import qrcode
        tid = (self.state.get("track") or {}).get("id", "")
        url = "https://open.spotify.com/track/"+tid if re.fullmatch(r"[A-Za-z0-9]{22}",tid) else "https://open.spotify.com/"
        qr = qrcode.QRCode(border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(url); qr.make(fit=True)
        matrix = qr.get_matrix(); n = len(matrix)
        img = QImage(n,n,QImage.Format.Format_RGB32)
        for y,row in enumerate(matrix):
            for x,black in enumerate(row):
                img.setPixelColor(x,y,QColor("black" if black else "white"))
        buffer = QBuffer(); buffer.open(QIODevice.OpenModeFlag.WriteOnly); img.save(buffer,"PNG")
        self.set_view(qrImage="data:image/png;base64,"+base64.b64encode(bytes(buffer.data())).decode(),qrUrl=url)

    @Slot()
    def disconnectSpotify(self):
        self.signed_out = True
        self.logout_pending = True
        backend.CLIENT_ID = ""
        def clear_credentials():
            try:
                # Wait outside the GUI thread for any in-flight token refresh.
                with backend._refresh_lock:
                    Path(backend.TOKENS).unlink(missing_ok=True)
                    with backend._tokens_lock:
                        backend._tokens_cache["data"] = None
                self.incoming.emit({"kind":"logout_done"})
            except OSError:
                self.incoming.emit({"kind":"logout_done", "error":True})
        threading.Thread(target=clear_credentials,daemon=True).start()
        self.state = {}; self.raw_lyrics = []; self.loaded_track = None
        self.clock.update(0,False,None); self.want_audio.clear(); self.clearPulse.emit()
        self.line_key = None
        self.apply_music_preset()
        self.set_view(loggedIn=False,playing=False,title="Conecta Spotify",artist="FIESTA",cover="",queue="",status="DESCONECTADO",message="Sesión local desconectada.")

    @Slot()
    def tapBeat(self):
        if not self.clock.playing:
            return
        now = time.monotonic()
        if self.taps and now-self.taps[-1][0] > 2:
            self.taps = []
        self.taps = (self.taps + [(now, self.clock.read())])[-8:]
        if len(self.taps) >= 4:
            n = len(self.taps)
            center = (n-1)/2
            period = sum((i-center)*tap[0] for i, tap in enumerate(self.taps)) / sum((i-center)**2 for i in range(n))
            if .25 <= period <= 1.5:
                c = dict(self.calibration())
                c.update(bpm=60/period, anchor=sum(p-i*period for i, (_, p) in enumerate(self.taps))/n)
                self.track_settings[self.clock.track] = c
                self.save_timer.start(300)
                self.set_view(message=f"Calibrado: {60/period:.1f} BPM. Selecciona Mapa / calibración para usarlo.")
        else:
            self.set_view(message=f"Marcando: {len(self.taps)}/4 golpes")

    @Slot()
    def resetRhythm(self):
        self.track_settings.pop(self.clock.track, None)
        self.taps = []
        self.refresh_profile()
        self.scheduler.reset(time.monotonic())
        self.grid_cursor = -1
        self.save_timer.start(300)

    @Slot()
    def openTranslation(self):
        self.translation_active = True
        self.line_key = None
        self.openSecond.emit()

    @Slot()
    def translationClosed(self):
        self.translation_active = False

    @Slot(str)
    def connectSpotify(self, client_id):
        if self.logout_pending:
            self.set_view(message="Terminando la desconexión; espera un momento.")
            return
        client_id = client_id.strip()
        if client_id:
            if not re.fullmatch(r"[A-Fa-f0-9]{32}", client_id):
                self.set_view(message="El Client ID de Spotify debe tener 32 caracteres hexadecimales.")
                return
            try:
                Path(backend.CONFIG).write_text(json.dumps({"client_id": client_id}), encoding="utf-8")
                backend.CLIENT_ID = client_id
            except OSError:
                self.set_view(message="No se pudo guardar el Client ID.")
                return
        if not backend.CLIENT_ID:
            backend.CLIENT_ID = backend.load_client_id()
        if not backend.CLIENT_ID:
            self.set_view(message="Introduce tu Client ID de Spotify para conectar.")
            return
        # Only authorization opens a browser, never the visualizer/rendering.
        try:
            if not getattr(self, "auth_server", None):
                # A dedicated OAuth-only handler does not serve the web visualizer.
                class AuthHandler(backend.Handler):
                    def do_GET(self):
                        u = urllib.parse.urlparse(self.path)
                        if u.path == "/login":
                            self._login(u)
                        elif u.path == "/callback":
                            self._callback(u)
                        elif u.path == "/":
                            self._html("<h2>FIESTA</h2><p>Ya puedes cerrar esta pestaña y volver a la aplicación.</p>")
                        else:
                            self._send(404, "Not found", "text/plain")
                if backend.port_in_use(backend.PORT):
                    self.set_view(message=f"El puerto {backend.PORT} está ocupado. Cierra el servidor web de FIESTA antes de reconectar Spotify. La sesión importada sigue disponible.")
                    return
                auth = backend.Server(("127.0.0.1", backend.PORT), AuthHandler)
                threading.Thread(target=auth.serve_forever, daemon=True).start()
                self.auth_server = auth
            QDesktopServices.openUrl(QUrl(f"http://127.0.0.1:{backend.PORT}/login"))
            self.signed_out = False
            self.set_view(message=f"Autoriza Spotify. Redirect URI: {backend.REDIRECT_URI}")
        except OSError as exc:
            self.set_view(message="No se pudo abrir la autorización: " + str(exc))

    @Slot()
    def shutdown(self):
        self.stop.set()
        self.want_audio.clear()
        self.timer.stop()
        self.save()

    def enqueue(self, job):
        try:
            self.jobs.put_nowait(job)
        except queue.Full:
            if job[0] == "translate":
                self.translation_pending.discard(job[1])

    def playback_worker(self):
        track = None
        demo = False
        next_meta = 0
        while not self.stop.is_set():
            if self.signed_out:
                track = None
                self.stop.wait(.25)
                continue
            try:
                if track is None or demo:
                    state = backend.build_state()
                    track = (state.get("track") or {}).get("id")
                    demo = state.get("demo", False)
                    self.incoming.emit({"kind": "state", "data": state, "received_at": time.monotonic()})
                else:
                    sync = backend.sync_state()
                    if sync.get("track_id") != track:
                        self.incoming.emit({"kind": "loading", "track": sync.get("track_id")})
                        state = backend.build_state()
                        track = (state.get("track") or {}).get("id")
                        demo = state.get("demo", False)
                        self.incoming.emit({"kind": "state", "data": state, "received_at": time.monotonic()})
                    else:
                        self.incoming.emit({"kind": "clock", "data": sync, "received_at": time.monotonic()})
                if time.monotonic() > next_meta:
                    next_meta = time.monotonic()+15
                    self.enqueue(("queue",))
            except Exception as exc:
                self.incoming.emit({"kind": "error", "text": "Spotify: " + str(exc)[:180]})
            self.stop.wait(1 if demo or track is None else .25)

    def audio_worker(self):
        sequence = None
        try:
            while not self.stop.is_set():
                if not self.want_audio.wait(.2):
                    if sequence is not None:
                        loopback.unsubscribe()
                        sequence = None
                    continue
                if sequence is None:
                    sequence = loopback.subscribe()
                next_sequence, packet = loopback.wait(sequence, .2)
                if next_sequence != sequence:
                    sequence = next_sequence
                    packet["received_at"] = time.monotonic()
                    self.incoming.emit({"kind": "audio", "data": packet})
        finally:
            if sequence is not None:
                loopback.unsubscribe()

    def job_worker(self):
        artist_cache = {}
        cover_cache = {}
        while not self.stop.is_set():
            try:
                job = self.jobs.get(timeout=.25)
            except queue.Empty:
                continue
            try:
                if self.signed_out and job[0] != "translate":
                    continue
                if job[0] == "cover":
                    track, url = job[1:]
                    if url not in cover_cache:
                        code, data = backend.request(url, timeout=5)
                        img = QImage.fromData(data) if code == 200 and isinstance(data,bytes) else QImage()
                        colors = []
                        if not img.isNull():
                            img = img.scaled(24,24)
                            buckets = Counter((img.pixelColor(x,y).red()//32,img.pixelColor(x,y).green()//32,img.pixelColor(x,y).blue()//32)
                                              for y in range(24) for x in range(24))
                            colors = ["#%02x%02x%02x" % tuple(c*32+16 for c in rgb) for rgb,_ in buckets.most_common(5)]
                        cover_cache[url] = (colors*5)[:5] if colors else list(DEFAULTS["customPalCols"])
                        if len(cover_cache)>100:
                            cover_cache.pop(next(iter(cover_cache)))
                    self.incoming.emit({"kind":"cover", "track":track, "colors":cover_cache[url]})
                elif job[0] == "translate":
                    key, text, source, target = job[1:]
                    if source == target or not any(c.isalpha() for c in text):
                        translated = text
                    else:
                        query = urllib.parse.urlencode({"q": text, "langpair": source+"|"+target})
                        code, data = backend.request("https://api.mymemory.translated.net/get?"+query, timeout=8)
                        if code != 200 or str((data or {}).get("responseStatus")) != "200" or (data or {}).get("quotaFinished"):
                            raise RuntimeError("Servicio de traducción no disponible o cuota agotada")
                        translated = html.unescape(data["responseData"]["translatedText"])
                    self.incoming.emit({"kind": "translation", "key": key, "text": translated})
                elif job[0] == "genre":
                    track, ids = job[1:]
                    tags = []
                    for artist in ids[:3]:
                        if artist not in artist_cache and backend.api_allow():
                            token = backend.access_token()
                            if not token:
                                continue
                            code, data = backend.request("https://api.spotify.com/v1/artists/"+urllib.parse.quote(artist),
                                                         headers={"Authorization": "Bearer "+token}, timeout=3)
                            artist_cache[artist] = (data or {}).get("genres", []) if code == 200 else []
                            if len(artist_cache) > 400:
                                artist_cache.pop(next(iter(artist_cache)))
                        tags.extend(artist_cache.get(artist, []))
                    self.incoming.emit({"kind": "genre", "track": track, "data": classify_genres(tags)})
                elif job[0] == "queue" and backend.api_allow():
                    token = backend.access_token()
                    if token:
                        code, data = backend.request("https://api.spotify.com/v1/me/player/queue", headers={"Authorization": "Bearer "+token}, timeout=3)
                        items = (data or {}).get("queue", []) if code == 200 else []
                        text = (items[0].get("name", "") + " — " + ", ".join(a.get("name","") for a in items[0].get("artists",[]))) if items else ""
                        self.incoming.emit({"kind": "queue", "text": text})
            except Exception as exc:
                if job[0] == "translate":
                    self.incoming.emit({"kind": "translation", "key": job[1], "text": "", "error": str(exc)[:100]})

    @Slot(object)
    def receive(self, packet):
        if self.stop.is_set():
            return
        kind, now = packet["kind"], time.monotonic()
        if self.signed_out and kind in ("loading","state","clock","queue","genre","cover"):
            return
        if kind == "logout_done":
            self.logout_pending = False
            if packet.get("error"):
                self.set_view(message="No se pudo borrar la credencial local; revisa los permisos de la carpeta de datos.")
        elif kind == "loading":
            self.loading_track = True
            self.clock.update(0, False, None)
            self.state = {}
            self.line_key = None
            self.scheduler.reset(now)
            self.clearPulse.emit()
            self.set_view(playing=False, title="Cargando canción…", artist="Spotify", cover="")
        elif kind in ("state", "clock"):
            data = packet["data"]
            track = (data.get("track") or {}).get("id") if kind == "state" else data.get("track_id")
            playing = bool(data.get("is_playing"))
            position = data.get("progress_ms", 0)/1000
            if playing:
                position += max(0, now-data.get("position_at", packet["received_at"]))
            changed = self.clock.track != track
            reset = self.clock.update(position, playing, track)
            if reset:
                self.scheduler.reset(now)
                self.grid_cursor = -1
                self.section_cursor = -1
                self.clearPulse.emit()
            if kind == "state":
                lyrics_changed = self.raw_lyrics != data.get("lyrics", [])
                previous_lines = self.state.get("lyrics", [])
                self.state = data
                t = data.get("track") or {}
                self.raw_lyrics = copy.deepcopy(data.get("lyrics", []))
                self.set_view(title=t.get("name", "Reproduce una canción"), artist=t.get("artist", "Spotify"),
                              cover=t.get("cover") or "", duration=t.get("duration_ms", 0)/1000,
                              demo=bool(data.get("demo")), loggedIn=bool(data.get("logged_in")),
                              lyricSource=(data.get("lyrics") or [{}])[0].get("source", "Letra sincronizada"),
                              status="DEMO · conecta Spotify" if data.get("demo") else "SPOTIFY · SINCRONIZADO" if t else "ESPERANDO SPOTIFY")
                if data.get("error"):
                    self.set_view(status={"premium":"Spotify requiere Premium", "reconnect":"Sesión expirada · reconecta Spotify", "ratelimit":"Spotify limita las consultas · esperando"}.get(data["error"],"Spotify no disponible"))
                if changed:
                    self.evidence = {"genre": "unknown"}
                    self.taps = []
                    self.enqueue(("genre", track, t.get("artist_ids", [])))
                    self.line_key = None
                if self.loaded_track != track:
                    if self.loaded_track and track and not self._settings["reducedMotion"]:
                        self.transitionRequested.emit(self._settings["transition"])
                    self.loaded_track = track
                    self.cover_palette = list(DEFAULTS["customPalCols"])
                    self.apply_music_preset()
                    if t.get("cover"):
                        self.enqueue(("cover",track,t["cover"]))
                    if self._settings["qrEnabled"]:
                        self.prepareQR()
                elif lyrics_changed:
                    self.rephrase()
                else:
                    self.state["lyrics"] = previous_lines
                self.loading_track = False
                self.refresh_profile()
            self.set_view(playing=playing)
        elif kind == "audio":
            data = packet["data"]
            if not self.want_audio.is_set():
                return
            if data.get("state") == "listening":
                bpm = data.get("bpm") if now-self.scheduler.context_at >= 8 else None
                self.set_view(audio=(data.get("device", "Salida Windows") + (" · audio" if data.get("level", 0) > .001 else " · silencio")), bpm=bpm or 0)
                self.scheduler.ingest(data, now, self.genre(), self._settings["threshold"],
                                      self.calibration().get("offset", 0), self._settings["timing"])
                pulse = self.scheduler.due(now)
                if pulse:
                    self.emit_pulse(pulse)
            else:
                self.set_view(audio=data.get("reason", "Preparando salida WASAPI…"), bpm=0)
        elif kind == "genre" and packet["track"] == self.clock.track:
            self.evidence = packet["data"]
            self.refresh_profile()
        elif kind == "cover" and packet["track"] == self.clock.track:
            self.cover_palette = packet["colors"]
            self.refresh_profile()
        elif kind == "translation":
            self.translation_pending.discard(packet["key"])
            self.translation_cache[packet["key"]] = (packet["text"], packet.get("error", ""))
            if len(self.translation_cache) > 400:
                self.translation_cache.pop(next(iter(self.translation_cache)))
            self.update_translation()
        elif kind == "queue":
            self.set_view(queue=packet["text"])
        elif kind == "error":
            self.set_view(status=packet["text"])

    def emit_pulse(self, pulse):
        if not self._settings["reducedMotion"] and self.clock.playing and self.windows_active:
            palette = PALETTES[self._settings["palette"]]
            color = "#ffffff" if self._settings["pulseWhite"] else palette[self.color_cursor % len(palette)]
            self.color_cursor += 1
            self.pulse.emit(pulse["age"], pulse["duration"], color, pulse.get("drop", False))

    def translation_key(self, text):
        return "|".join((self._settings["fromLang"], self._settings["toLang"], text))

    def update_translation(self):
        if not self.translation_active:
            return
        text = self._lyric["text"]
        key = self.translation_key(text)
        translated, error = self.translation_cache.get(key, ("", ""))
        if not translated and not error and key not in self.translation_pending:
            self.translation_pending.add(key)
            self.enqueue(("translate", key, text, self._settings["fromLang"], self._settings["toLang"]))
        self._lyric.update(translated=translated or ("Traducción no disponible" if error else "Traduciendo…"), translationStatus=error)
        self.lyricChanged.emit()

    @Slot()
    def tick(self):
        now = time.monotonic()
        live = self._settings["source"] == "loopback" and not self.state.get("demo")
        active = self.clock.playing and self.windows_active and not self._settings["reducedMotion"]
        if live and active:
            self.want_audio.set()
        else:
            self.want_audio.clear()
        if not active:
            self.scheduler.queue.clear()
        if now-self.last_position_emit >= .05:
            self.last_position_emit = now
            self._position = self.clock.read()
            self.positionChanged.emit()
        position = self.clock.read()
        lines = self.state.get("lyrics", [])
        index = active_line(lines, position)
        title = position < 7 or index < 0
        key = (self.clock.track, index, title, self._settings["fromLang"], self._settings["toLang"])
        if key != self.line_key:
            self.line_key = key
            self.line_index = index
            line = lines[index] if index >= 0 and not title else {}
            text = line.get("text", self._view["title"])
            self._lyric = dict(text=text, back=line.get("back") or "",
                               groups=word_groups(line.get("words")), title=title,
                               egg=egg_kind(text) if not title and self._settings["easterEggs"] else "", start=line.get("t",position),
                               translated="", translationStatus="")
            self.lyricChanged.emit()
            self.update_translation()
            if self.translation_active:
                for next_line in lines[max(0,index+1):index+4]:
                    text = next_line.get("text", "")
                    k = self.translation_key(text)
                    if k not in self.translation_cache and k not in self.translation_pending:
                        self.translation_pending.add(k)
                        self.enqueue(("translate", k, text, self._settings["fromLang"], self._settings["toLang"]))
        if not active:
            return
        if live:
            pulse = self.scheduler.due(now)
            if pulse:
                self.emit_pulse(pulse)
        else:
            c = self.calibration()
            bpm = c.get("bpm") or self.state.get("tempo", 120)
            position += c.get("offset", 0)/1000
            if c.get("bpm"):
                step = 60/bpm * (4 if self._settings["timing"] == "bars" else 1)
                i = int((position-c.get("anchor", 0)) // step)
                at = c.get("anchor", 0) + i*step
                if self._settings["timing"] == "sections":
                    return
            else:
                times = self.state.get(self._settings["timing"], [])
                if self._settings["timing"] == "sections" and not (self.state.get("demo") or self.state.get("rhythm_source") == "spotify"):
                    times = []
                i = bisect.bisect_right(times, position)-1
                at = times[i] if i >= 0 else -100
            if i != self.grid_cursor:
                self.grid_cursor = i
                if 0 <= position-at <= .08:
                    self.emit_pulse(dict(age=position-at, duration=.94*60/bpm, color=PALETTE[i % len(PALETTE)]))
            self.set_view(audio="Mapa calibrado" if c.get("bpm") else "Análisis Spotify" if self.state.get("rhythm_source") == "spotify" else "Ritmo estimado · no es percusión detectada", bpm=bpm)
            sections = self.state.get("sections", []) if self.state.get("demo") or self.state.get("rhythm_source") == "spotify" else []
            section = bisect.bisect_right(sections,position)-1
            if section != self.section_cursor:
                self.section_cursor = section
                if section >= 0 and 0 <= position-sections[section] <= .08 and self._settings["dropFx"]:
                    self.dropRequested.emit()

    @staticmethod
    def smoke_state():
        return dict(demo=True, is_playing=True, progress_ms=8500, tempo=120, mood="party",
                    track=dict(id="native-smoke", name="FIESTA NATIVO", artist="GPU · sin navegador", duration_ms=120000),
                    lyrics=[dict(t=0, text="FIESTA NATIVO"), dict(t=7, text="Siente el ritmo", words=[
                        dict(text="Siente", t=8, end=10), dict(text="el", t=10, end=11), dict(text="ritmo", t=11, end=13)])],
                    beats=[i*.5 for i in range(240)], bars=list(range(0,120,2)), sections=[])
