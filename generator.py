from typing import List, Dict, Any, Optional

import requests
import logging

from tools.spotify_api_tools import SpotifyAPITools

logger = logging.getLogger("uvicorn")

def generate(genres: List[str]):
    verified_artists = []

    while len(verified_artists) < 3:
        band = _get_random_band()

        if not band:
            continue

        band_name = band.get("name")
        band_genres = band.get("genres", [])

        if not _matches_genres(band_genres, genres):
            continue

        logger.info("Genre match! Checking availability in Spotify")
        spotify_artist = SpotifyAPITools.get_artist(band_name)
        if not spotify_artist:
            continue

        logger.info("Added verified artist")
        verified_artists.append(spotify_artist)

    logger.info("Getting tracks")
    tracks = SpotifyAPITools.get_tracks(verified_artists)

    logger.info("Creating playlist")
    SpotifyAPITools.create_playlist("Test", "test", tracks)

def _get_random_band() -> Optional[Dict[str, Any]]:
    url = "https://api.metal-map.com/v1/random"

    logger.info("Getting random band")
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.warning(f"Failed to get random band: {response.status_code}")
            return None

        data = response.json()
        logger.info(f"Response: {data}")

        if not isinstance(data, list) or not data:
            return None

        band = data[0]

        name = band.get("name")
        genre = band.get("genre")

        # Normalize to your expected structure
        genres_list = [genre] if genre else []

        logger.info(f"Name: {name}")
        logger.info(f"Genres: {genres_list}")
        return {
            "name": name,
            "genres": genres_list
        }

    except RuntimeError:
        return None



def _matches_genres(band_genres: List[str], selected_genres: List[str]) -> bool:
    logger.info("Checking if genres match")

    band_genres_lower = [g.lower() for g in band_genres]
    selected_lower = [g.lower() for g in selected_genres]

    return any(
        sel in genre
        for sel in selected_lower
        for genre in band_genres_lower
    )

