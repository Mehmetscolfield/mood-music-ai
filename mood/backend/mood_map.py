# --- Mood → Spotify recommendation parameters (stable, broad seeds) ---
MOOD_TO_SPOTIFY = {
    "happy":       {"seed_genres": "pop,edm,latin,indie,rock",      "target_valence": 0.85, "target_energy": 0.7},
    "energetic":   {"seed_genres": "edm,rock,hip-hop,pop,indie",    "target_valence": 0.7,  "target_energy": 0.9},
    "calm":        {"seed_genres": "acoustic,ambient,chill,indie",  "target_valence": 0.6,  "target_energy": 0.25},
    "peaceful":    {"seed_genres": "acoustic,ambient,chill,piano",  "target_valence": 0.65, "target_energy": 0.2},
    "romantic":    {"seed_genres": "r-n-b,soul,acoustic,pop",       "target_valence": 0.8,  "target_energy": 0.4},
    "melancholic": {"seed_genres": "indie,folk,alt-rock,acoustic",  "target_valence": 0.3,  "target_energy": 0.35},
    "sad":         {"seed_genres": "indie,folk,pop,acoustic",       "target_valence": 0.2,  "target_energy": 0.25},
    "angry":       {"seed_genres": "metal,hard-rock,hip-hop,rock",  "target_valence": 0.3,  "target_energy": 0.95},
}
DEFAULT_MOOD = "calm"
CANDIDATE_MOODS = list(MOOD_TO_SPOTIFY.keys())

# Language → which Spotify market (catalog) to prefer
LANGUAGE_MARKET = {
    "english":  "US",
    "turkish":  "TR",
    "korean":   "KR",
    "japanese": "JP",
    "spanish":  "ES",
    "arabic":   "AE",
}
DEFAULT_MARKET = "US"
DEFAULT_LANGUAGE = "english"
