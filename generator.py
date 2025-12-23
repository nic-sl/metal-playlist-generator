import requests

from typing import List, Dict, Any, Optional

from logging_stream import log
from tools.spotify_api_tools import SpotifyAPITools


def generate(genres: List[str], artist_count: int, track_count: int):
    verified_artists = []

    while len(verified_artists) < artist_count:
        band = _get_random_band()

        if not band:
            continue

        band_name = band.get("name")
        band_genres = band.get("genres", [])

        if not _matches_genres(band_genres, genres):
            log("Genre mismatch, skipping.")
            continue

        log("Checking availability in Spotify.")
        spotify_artist = SpotifyAPITools.get_artist(band_name)
        if not spotify_artist:
            log("Artist not found in Spotify, skipping.")
            continue

        log("Added Spotify-verified artist.")
        verified_artists.append(spotify_artist)

    log(f"Getting the top {track_count} track(s) from each artist.")
    tracks = SpotifyAPITools.get_tracks(verified_artists, track_count)

    name = generate_playlist_name(selected_genres=genres)
    description = generate_playlist_description(selected_genres=genres)
    log(f"Creating playlist {name}.")
    SpotifyAPITools.create_playlist(name, description, tracks)


def _get_random_band() -> Optional[Dict[str, Any]]:
    url = "https://api.metal-map.com/v1/random"

    log("Getting random band using Metal Map API.")
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            log(f"Failed to get random band: {response.status_code}.")
            return None

        data = response.json()

        if not isinstance(data, list) or not data:
            return None

        band = data[0]

        name = band.get("name")
        genre = band.get("genre")

        # Normalize to your expected structure
        genres_list = [genre] if genre else []

        log(f"Name: {name}")
        log(f"Genres: {genres_list}")
        return {
            "name": name,
            "genres": genres_list
        }

    except RuntimeError:
        return None



def _matches_genres(band_genres: List[str], selected_genres: List[str]) -> bool:
    log("Checking if band genres match selected genres.")

    if not selected_genres:
        log("User did not select any genres, so all bands are valid.")
        return True

    band_genres_lower = [g.lower() for g in band_genres]
    selected_lower = [g.lower() for g in selected_genres]

    return any(
        sel in genre
        for sel in selected_lower
        for genre in band_genres_lower
    )

def generate_playlist_description(selected_genres: list[str]) -> str:
    if selected_genres:
        if len(selected_genres) == 1:
            genre_text = selected_genres[0]
        else:
            genre_text = ", ".join(selected_genres[:-1]) + " and " + selected_genres[-1]

        return f"A crushing selection of {genre_text} metal tracks."

    return "A diverse metal playlist forged for true headbangers."

import random

def generate_playlist_name(selected_genres: list[str]) -> str:
    metal_words = [
        "Rituals", "Abyss", "Storms", "Dominion", "Legion", "Cataclysm",
        "Requiem", "Sanctum", "Inferno", "Monolith", "Eclipse", "Ascension",
        "Annihilation", "Odyssey", "Revolt", "Rebirth"
    ]

    if selected_genres:
        genre = random.choice(selected_genres)
        word = random.choice(metal_words)
        return f"{genre} {word}"

    # If no genres selected, use generic metal names
    generic_prefixes = [
        "Metal", "Heavy", "Dark", "Iron", "Steel", "Forged", "Unholy"
    ]
    prefix = random.choice(generic_prefixes)
    word = random.choice(metal_words)
    return f"{prefix} {word}"


