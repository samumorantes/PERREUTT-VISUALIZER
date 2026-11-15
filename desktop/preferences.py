"""Validated native preferences and the web edition's themes/preset semantics."""
import colorsys
import math
import re

DEFAULTS = dict(mood="auto", source="loopback", timing="beats", strength=85.0,
                threshold=1.75, lens=12.0, scan=70.0, mask=60.0, vignette=70.0,
                grain=30.0, fontSize=7.0, font="arcade", tv=True, reducedMotion=False,
                fluidStyle=0, quality=1.0, fromLang="es", toLang="en",
                theme="classic", palette="rgb", phrase=4, wordSpacing=1.0, upper=False,
                stroke=2.0, shadow=50.0, pulseColor=True, pulseWhite=False,
                autoMood=True, trails=True, spectrum=False, beatBounce=False, dropFx=True,
                smartContrast=True, qrEnabled=False, autoQuality=True, scanOn=True,
                flicker=True, tilt=True, refresh=True, fish=True, transition="tv",
                customPal=False, customPalCols=["#5a2a91", "#8f3f7d", "#2a6b91", "#c46a3f", "#3f915a"],
                globalLock=False, easterEggs=True)
RANGES = {"strength": (0,100), "threshold": (1.5,10), "lens": (0,100),
          "scan": (0,100), "mask": (0,100), "vignette": (0,100), "grain": (0,100),
          "fontSize": (3,16), "quality": (.5,1), "fluidStyle": (0,3), "phrase": (1,4),
          "wordSpacing": (0,3), "stroke": (0,6), "shadow": (0,100)}
ENUMS = {"mood": ("auto","party","chill"), "source": ("loopback","grid"),
         "timing": ("beats","bars","sections"),
         "font": ("arcade","grotesk","impact","courier","georgia","system"),
         "fromLang": ("es","en","fr","pt","it","de"), "toLang": ("es","en","fr","pt","it","de"),
         "theme": ("classic","vaporwave","matrix","snes"),
         "palette": ("rgb","pastel","neon","sunset","ocean","byn"),
         "transition": ("tv","shutter","vinyl","flashcolor","none")}
THEMES = {
    "classic": dict(palette="rgb",font="arcade",scanOn=True,scan=70,mask=60,vignette=70,grain=50,flicker=True,tilt=True,refresh=True,fish=True),
    "vaporwave": dict(palette="sunset",font="georgia",scanOn=True,scan=85,mask=30,vignette=80,grain=35,flicker=False,tilt=True,refresh=True,fish=True),
    "matrix": dict(palette="ocean",font="courier",scanOn=True,scan=90,mask=15,vignette=85,grain=65,flicker=True,tilt=False,refresh=True,fish=True),
    "snes": dict(palette="neon",font="arcade",scanOn=False,scan=0,mask=45,vignette=45,grain=25,flicker=False,tilt=False,refresh=False,fish=False),
}
PALETTES = {
    "rgb": ["#ff1744","#ff6d00","#ffd600","#00e676","#00b0ff","#651fff","#d500f9"],
    "pastel": ["#f584aa","#f8bd81","#f4e97b","#7de8b2","#84cefa","#c5a0f4"],
    "neon": ["#ff1ab2","#aa33ff","#00d4ff","#00ff00","#ffea1a","#ff531a"],
    "sunset": ["#fa2e3f","#ff7733","#ffbe3d","#e54dc9","#b451ec"],
    "ocean": ["#0687e0","#0bcccb","#256af4","#12e2ae","#4747eb"],
    "byn": ["#ffffff","#999999","#dddddd","#666666"],
}
DARK_DEEP = ["#120a2d", "#1e0f46", "#08193c", "#32145a", "#0c2350"]
PRESET_KEYS = set(DEFAULTS) - {"mood","autoQuality","quality","source","threshold","fromLang","toLang","globalLock","reducedMotion"}
WEB_KEYS = dict(fs="fontSize",lensStrength="lens",mode="palette",flashStrength="strength",vig="vignette",noise="grain",moodOverride="mood")

def clean_setting(key, value):
    if key in RANGES:
        if isinstance(value, bool):
            return None
        try:
            v = float(value)
            if not math.isfinite(v):
                return None
            v = max(RANGES[key][0], min(RANGES[key][1], v))
            return round(v) if key in ("phrase","fluidStyle") else v
        except (TypeError, ValueError):
            return None
    if key in ENUMS:
        return value if isinstance(value,str) and value in ENUMS[key] else None
    if key == "customPalCols":
        if isinstance(value,list) and len(value)==5 and all(isinstance(c,str) and re.fullmatch(r"#[0-9a-fA-F]{6}",c) for c in value):
            return list(value)
        return None
    if isinstance(DEFAULTS.get(key),bool) and isinstance(value,bool):
        return value
    return None

def validate(values, web=False):
    out = {}
    if not isinstance(values,dict):
        return out
    for key,value in values.items():
        key = WEB_KEYS.get(key,key) if web else key
        if web and key == "fluidStyle" and isinstance(value,str):
            value = {"flow":0,"swirl":1,"plasma":2,"aurora":3}.get(value,-1)
        clean = clean_setting(key,value)
        if clean is not None:
            out[key] = clean
    return out

def preset_keys(track):
    if not track:
        return {}
    return {"song": "song:"+str(track.get("id") or track.get("name", "")),
            "artist": "artist:"+track.get("artist", ""),
            "album": "album:"+track.get("artist", "")+"|"+track.get("album", "")}

def find_preset(store, track):
    keys = preset_keys(track)
    candidates = [keys.get("song"), "song:"+track.get("name", ""), keys.get("artist"),
                  keys.get("album"), "album:"+track.get("album", "")]
    return next(((key,store[key]) for key in candidates if key in store), None)

def is_special(track):
    return bool(re.search(r"die\s*for\s*you",track.get("name",""),re.I) and re.search("joji",track.get("artist",""),re.I))

def egg_kind(text):
    if re.search(r"\bEOOO?\b",text,re.I):
        return "eoo"
    return "impact" if re.search(r"Perreo|Tra-tra|Chequ[eé]ate la historia",text,re.I) else ""

def random_palette(rng):
    return ["#%02x%02x%02x" % tuple(round(c*255) for c in colorsys.hls_to_rgb(rng.random(),.4+rng.random()*.2,.65)) for _ in range(5)]
