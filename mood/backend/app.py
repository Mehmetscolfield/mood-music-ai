import os, time, random, math, traceback
from typing import List, Tuple, Dict
from PIL import Image
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
from deepface import DeepFace
import cv2

# =============== CONFIG ===============
LANG_TO_MARKET = {
    "english":"US","turkish":"TR","korean":"KR","japanese":"JP","spanish":"ES","arabic":"AE"
}
DEFAULT_LANGUAGE, DEFAULT_MARKET = "english", "US"
DEFAULT_MOOD = "happy"

# Curated popular seed artists per language+mood
POPULAR_SEEDS: Dict[str, Dict[str, List[str]]] = {
    "turkish": {
        "happy":       ["Lvbel C5", "Semicenk", "Hadise", "Tarkan", "Mabel Matiz"],
        "energetic":   ["Ezhel", "UZI", "Ceza", "Reynmen", "Edis"],
        "romantic":    ["Yalın", "Melike Şahin", "Mabel Matiz"],
        "sad":         ["Sezen Aksu", "Duman", "Teoman", "Manuş Baba"],
        "melancholic": ["Duman", "Mor ve Ötesi", "Teoman"],
        "calm":        ["Kalben", "Cem Adrian"],
        "peaceful":    ["Cem Adrian", "Yüzyüzeyken Konuşuruz"],
        "angry":       ["Sagopa Kajmer", "Ceza", "UZI"],
    },
    "korean": {
        "happy":       ["NewJeans", "IVE", "SEVENTEEN", "TWICE", "LE SSERAFIM"],
        "energetic":   ["BTS", "Stray Kids", "ATEEZ", "BLACKPINK"],
        "romantic":    ["IU", "BOL4"],
        "sad":         ["AKMU", "Baek Yerin", "Epik High"],
        "melancholic": ["Heize", "10CM"],
        "calm":        ["IU", "Paul Kim"],
        "peaceful":    ["AKMU", "Jannabi"],
        "angry":       ["Stray Kids", "ATEEZ"],
    },
    "japanese": {
        "happy":       ["YOASOBI", "Official髭男dism", "TWICE"],
        "energetic":   ["Mrs. GREEN APPLE", "UVERworld"],
        "romantic":    ["Aimer", "back number"],
        "sad":         ["Aimer", "YUI"],
        "melancholic": ["Kenshi Yonezu", "RADWIMPS"],
        "calm":        ["Kenshi Yonezu", "Aimer"],
        "peaceful":    ["RADWIMPS", "Aimer"],
        "angry":       ["ONE OK ROCK"],
    },
    "spanish": {
        "happy":       ["Bad Bunny", "Karol G", "Shakira", "Rauw Alejandro"],
        "energetic":   ["J Balvin", "Peso Pluma", "Bad Bunny"],
        "romantic":    ["Morat", "Camilo"],
        "sad":         ["Pablo Alborán", "Aitana"],
        "melancholic": ["Morat", "Reik"],
        "calm":        ["Vicente García", "Jesse & Joy"],
        "peaceful":    ["Mon Laferte", "C. Tangana"],
        "angry":       ["Quevedo", "Eladio Carrión"],
    },
    "arabic": {
        "happy":       ["Amr Diab", "Nancy Ajram", "Saad Lamjarred"],
        "energetic":   ["Wegz", "Marwan Moussa"],
        "romantic":    ["Elissa", "Ragheb Alama"],
        "sad":         ["Fairuz", "Kadim Al Sahir"],
        "melancholic": ["Majida El Roumi", "Amr Diab"],
        "calm":        ["Hani Shaker", "Sherine"],
        "peaceful":    ["Fairuz", "Majida El Roumi"],
        "angry":       ["Wegz", "Balti"],
    },
    "english": {
        "happy":       ["Dua Lipa", "Harry Styles", "Justin Bieber", "Olivia Rodrigo"],
        "energetic":   ["The Weeknd", "Travis Scott", "David Guetta"],
        "romantic":    ["Taylor Swift", "Ed Sheeran"],
        "sad":         ["Billie Eilish", "Adele"],
        "melancholic": ["Lana Del Rey", "The Neighbourhood"],
        "calm":        ["Khalid", "Snoh Aalegra"],
        "peaceful":    ["Ludovico Einaudi", "Sufjan Stevens"],
        "angry":       ["Imagine Dragons", "Eminem"],
    },
}

# Global editorial (ultimate fallback)
GLOBAL_EDITORIAL = [
    "37i9dQZF1DXcBWIGoYBM5M",  # Today's Top Hits
    "37i9dQZEVXbLiRSasKsNU9",  # Viral 50 Global
    "37i9dQZEVXbMDoHDwVN2tF",  # Top 50 Global
]

CARDS_MAX = 12
WIDGETS_MAX = 8

# =============== APP / AUTH ===============
load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

_token, _exp = None, 0
def get_token() -> str:
    global _token, _exp
    now = time.time()
    if _token and now < _exp:
        return _token
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    _token, _exp = j["access_token"], now + j["expires_in"] - 30
    return _token

def sp_get(url: str, params: dict) -> dict:
    hdr = {"Authorization": f"Bearer {get_token()}"}
    r = requests.get(url, params=params, headers=hdr, timeout=25)
    r.raise_for_status()
    return r.json()

# =============== MOOD ===============
def image_to_mood(img: Image.Image) -> str:
    # DeepFace first
    try:
        rgb = np.array(img.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        res = DeepFace.analyze(
            bgr, actions=["emotion"], enforce_detection=False, detector_backend="opencv"
        )
        if isinstance(res, list) and res:
            res = res[0]
        emo = (res.get("dominant_emotion") or "").lower()
        mapping = {
            "angry": "angry",
            "disgust": "melancholic",
            "fear": "melancholic",
            "happy": "happy",
            "sad": "sad",
            "surprise": "energetic",
            "neutral": "calm",
        }
        mood = mapping.get(emo)
        if mood:
            return mood
    except Exception:
        pass

    # Fallback: simple color heuristic
    try:
        im = img.convert("RGB").resize((192, 192))
        arr = (np.asarray(im) / 255.0).reshape(-1, 3)
        r, g, b = arr[:, 0], arr[:, 1], arr[:, 2]
        mx = np.max(arr, axis=1)
        mn = np.min(arr, axis=1)
        diff = mx - mn + 1e-8
        h = np.zeros_like(mx)
        m = mx == r
        h[m] = (60 * ((g - b) / diff) % 360)[m]
        m = mx == g
        h[m] = (60 * (2 + (b - r) / diff))[m]
        m = mx == b
        h[m] = (60 * (4 + (r - g) / diff))[m]
        s = diff / (mx + 1e-8)
        v = mx
        S50, V50 = float(np.median(s)), float(np.median(v))
        Hmean = float(np.mean(h) % 360)
        if V50 < 0.22:
            return "sad"
        if S50 < 0.18:
            return "calm"
        if 20 <= Hmean < 80:
            return "happy"
        if Hmean >= 330 or Hmean < 20:
            return "angry"
        if 160 <= Hmean < 260:
            return "energetic"
        if 260 <= Hmean < 330:
            return "romantic"
        return "peaceful"
    except Exception:
        return DEFAULT_MOOD

# =============== Popular by Artist Seeds ===============
ARTIST_ID_CACHE: Dict[str, str] = {}

def resolve_artist_id(name: str, market: str) -> str:
    key = f"{name}|{market}"
    if key in ARTIST_ID_CACHE:
        return ARTIST_ID_CACHE[key]
    data = sp_get(
        "https://api.spotify.com/v1/search",
        {"q": name, "type": "artist", "market": market, "limit": 1},
    )
    items = data.get("artists", {}).get("items", [])
    if items:
        ARTIST_ID_CACHE[key] = items[0]["id"]
        return ARTIST_ID_CACHE[key]
    # try without market as fallback
    data = sp_get("https://api.spotify.com/v1/search", {"q": name, "type": "artist", "limit": 1})
    items = data.get("artists", {}).get("items", [])
    if items:
        ARTIST_ID_CACHE[key] = items[0]["id"]
        return ARTIST_ID_CACHE[key]
    return ""

def artist_top_tracks(artist_id: str, market: str) -> List[dict]:
    data = sp_get(f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks", {"market": market})
    return data.get("tracks", []) or []

def build_from_seeds(language: str, mood: str, market: str, max_tracks=60) -> List[dict]:
    names = (POPULAR_SEEDS.get(language) or {}).get(mood) or []
    pool = []
    random.shuffle(names)
    for name in names:
        try:
            aid = resolve_artist_id(name, market)
            if not aid:
                continue
            tt = artist_top_tracks(aid, market)
            for t in tt:
                if not t or not t.get("id"):
                    continue
                # keep any non-local track (do NOT drop by available_markets → avoids empty pools)
                if t.get("is_local"):
                    continue
                pool.append(t)
                if len(pool) >= max_tracks:
                    break
        except Exception:
            continue
        if len(pool) >= max_tracks:
            break

    # de-dupe by id
    seen, uniq = set(), []
    for t in pool:
        tid = t.get("id")
        if tid and tid not in seen:
            uniq.append(t)
            seen.add(tid)
    return uniq

# =============== Country fallbacks ===============
def featured_playlists(market: str) -> List[dict]:
    data = sp_get("https://api.spotify.com/v1/browse/featured-playlists", {"country": market, "limit": 20})
    return data.get("playlists", {}).get("items", [])

def toplist_playlists(market: str) -> List[dict]:
    cats = sp_get("https://api.spotify.com/v1/browse/categories", {"country": market, "limit": 50}).get(
        "categories", {}
    ).get("items", [])
    toplist_id = None
    for c in cats:
        if c.get("id") == "toplists":
            toplist_id = c["id"]
            break
    if not toplist_id:
        return []
    pls = sp_get(
        f"https://api.spotify.com/v1/browse/categories/{toplist_id}/playlists",
        {"country": market, "limit": 20},
    ).get("playlists", {}).get("items", [])
    return pls

def playlist_tracks(playlist_id: str, market: str, cap=100) -> List[dict]:
    items, url, params = [], f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", {
        "market": market, "limit": 100,
        "fields":"items(track(id,name,preview_url,artists(name),album(images),is_local)),next"
    }
    while url and len(items) < cap:
        data = sp_get(url, params)
        items.extend(data.get("items", []))
        url, params = data.get("next"), None
    tracks = [it.get("track") for it in items if it.get("track")]
    # keep all non-local tracks with id (don't drop by region; widgets still show)
    return [t for t in tracks if t and not t.get("is_local") and t.get("id")]

def country_toplist_widgets(market: str, need=WIDGETS_MAX) -> List[str]:
    try:
        pls = toplist_playlists(market)
        for pl in pls:
            tracks = playlist_tracks(pl["id"], market)
            ids = [t.get("id") for t in tracks if t and t.get("id")]
            if ids:
                random.shuffle(ids)
                return list(dict.fromkeys(ids))[:need]
        return []
    except Exception:
        return []

def country_featured_widgets(market: str, need=WIDGETS_MAX) -> List[str]:
    try:
        pls = featured_playlists(market)
        for pl in pls:
            tracks = playlist_tracks(pl["id"], market)
            ids = [t.get("id") for t in tracks if t and t.get("id")]
            if ids:
                random.shuffle(ids)
                return list(dict.fromkeys(ids))[:need]
        return []
    except Exception:
        return []

def global_editorial_widgets(need=WIDGETS_MAX) -> List[str]:
    try:
        ids = []
        for pid in GLOBAL_EDITORIAL:
            data = sp_get(f"https://api.spotify.com/v1/playlists/{pid}/tracks", {"limit": 100})
            for it in data.get("items", []):
                t = (it or {}).get("track") or {}
                if t.get("id"):
                    ids.append(t["id"])
        random.shuffle(ids)
        return list(dict.fromkeys(ids))[:need]
    except Exception:
        return []

def hardcoded_global_hits(need=8) -> List[str]:
    # Only used if all web calls fail, so UI never empties
    return [
        "0VjIjW4GlUZAMYd2vXMi3b",  # The Weeknd — Blinding Lights
        "7qiZfU4dY1lWllzX7mPBI3",  # Ed Sheeran — Shape of You
        "3KkXRkHbMCARz0aVfEt68P",  # Post Malone — Sunflower
        "6habFhsOp2NvshLv26DqMb",  # Dua Lipa — Levitating
        "4iJyoBOLtHqaGxP12qzhQI",  # The Weeknd — Save Your Tears
        "62aP9fBQKYKxi7PDXwcUAS",  # Olivia Rodrigo — good 4 u
        "2xLMifQCjDGFmkHkpNLD9h",  # Travis Scott — SICKO MODE
        "1fDsrQ23eTAVFElUMaf38X",  # backup id
    ][:need]

# =============== Shape cards ===============
def shape_cards(tracks: List[dict], max_items=CARDS_MAX) -> List[dict]:
    out, seen = [], set()
    for t in tracks:
        tid = t.get("id")
        if not tid or tid in seen:
            continue
        imgs = t.get("album", {}).get("images", [])
        img = imgs[1]["url"] if len(imgs) > 1 else (imgs[0]["url"] if imgs else "")
        out.append({
            "id": tid,
            "name": t.get("name", ""),
            "artists": ", ".join(a.get("name", "") for a in (t.get("artists") or [])),
            "image_url": img,
            "preview_url": t.get("preview_url") or ""
        })
        seen.add(tid)
        if len(out) >= max_items:
            break
    return out

# =============== API ===============
@app.post("/api/analyze")
def analyze():
    language = (request.form.get("language") or DEFAULT_LANGUAGE).strip().lower()
    market = LANG_TO_MARKET.get(language, DEFAULT_MARKET)

    # mood
    try:
        img = Image.open(request.files["image"].stream)
        mood = image_to_mood(img) or DEFAULT_MOOD
    except Exception:
        mood = DEFAULT_MOOD

    try:
        # Primary: popular artist seeds → top tracks
        seed_pool = build_from_seeds(language, mood, market, max_tracks=80)
        cards = shape_cards(seed_pool, max_items=CARDS_MAX)
        widgets = [t.get("id") for t in seed_pool if t.get("id")][:WIDGETS_MAX]

        # Strong fallbacks → widgets never empty
        if not widgets:
            widgets = (
                country_toplist_widgets(market, need=WIDGETS_MAX) or
                country_featured_widgets(market, need=WIDGETS_MAX) or
                global_editorial_widgets(need=WIDGETS_MAX)
            )
        if not widgets:  # absolute last resort
            widgets = hardcoded_global_hits(WIDGETS_MAX)

        return jsonify({"mood": mood, "language": language, "tracks": cards, "embeds": widgets})
    except Exception as e:
        traceback.print_exc()
        widgets = (
            country_toplist_widgets(market, need=WIDGETS_MAX) or
            country_featured_widgets(market, need=WIDGETS_MAX) or
            global_editorial_widgets(need=WIDGETS_MAX) or
            hardcoded_global_hits(WIDGETS_MAX)
        )
        return jsonify({"mood": mood, "language": language, "tracks": [], "embeds": widgets, "warning": str(e)}), 200

# Quick token/API sanity check
@app.get("/debug/spotify")
def debug_spotify():
    try:
        token = get_token()
        data = sp_get("https://api.spotify.com/v1/browse/featured-playlists", {"country": "US", "limit": 5})
        names = [p.get("name") for p in data.get("playlists", {}).get("items", [])]
        return {"ok": True, "got_token": bool(token), "featured_count": len(names), "sample": names}
    except Exception as e:
        traceback.print_exc()
        return {"ok": False, "error": str(e)}, 500

@app.get("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    print("[server] Popular seeds per language+mood → top-tracks; widgets guaranteed", flush=True)
    app.run(host="0.0.0.0", port=5050, debug=True)
