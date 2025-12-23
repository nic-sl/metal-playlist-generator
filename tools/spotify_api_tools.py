import os
import spotipy

from typing import List, Dict, Any
from spotipy.oauth2 import SpotifyClientCredentials

from logging_stream import log
from spotify_session.spotify_token_manager import SpotifyTokenManager
from spotify_session.spotify_app_user import SpotifyAppUser


# noinspection PyMethodParameters
class SpotifyAPITools:
    BASE_URL: str = "https://api.spotify.com/v1"

    @staticmethod
    def _get_app_client() -> spotipy.Spotify:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("Spotify client credentials not set in environment variables.")

        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        return spotipy.Spotify(auth_manager=auth_manager)

    @staticmethod
    def get_artist(artist_name: str) -> Dict[str, Any] | None:
        log(f"Searching for artist: {artist_name}")
        sp = SpotifyAPITools._get_app_client()

        search = sp.search(q=artist_name, type="artist", limit=10)
        items = search.get("artists", {}).get("items", [])

        exact_matches = [
            artist for artist in items
            if artist.get("name", "").lower() == artist_name.lower()
        ]

        if not exact_matches:
            log(f"No exact artist match found for '{artist_name}'")
            return None

        artist = exact_matches[0]
        log("Found exact artist. Returning its ID.")

        return artist.get("id")

    @staticmethod
    def _get_top_tracks(artist_uri: str) -> List[str]:
        sp = SpotifyAPITools._get_app_client()
        country = SpotifyAppUser.get_country()

        top = sp.artist_top_tracks(artist_uri, country=country)
        tracks = top.get("tracks", [])

        if not tracks:
            raise RuntimeError(
                f"[Spotify Top Tracks Error] No top tracks returned.\n"
                f"Artist URI: {artist_uri}\n"
                f"Full response: {top}"
            )

        uris = [t.get("uri") for t in tracks if t.get("uri")]
        if not uris:
            raise RuntimeError(
                f"[Spotify Top Tracks Error] Tracks returned but no URIs found.\n"
                f"Artist URI: {artist_uri}\n"
                f"Full response: {top}"
            )

        return uris

    @staticmethod
    def get_tracks(artist_uris: List[str], track_count: int) -> List[str]:  # NOSONAR
        all_tracks: List[str] = []

        for uri in artist_uris:
            top_uris = SpotifyAPITools._get_top_tracks(uri)
            top_3 = top_uris[:track_count]

            if not top_3:
                raise RuntimeError(
                    f"[Spotify Error] Artist '{uri}' returned no usable tracks."
                )

            all_tracks.extend(top_3)

        return all_tracks

    @staticmethod
    def create_playlist(playlist_name: str, playlist_description: str, track_uris: List[str]):  # NOSONAR
        token = SpotifyTokenManager.get_token()
        sp = spotipy.Spotify(auth=token)

        playlist = sp.user_playlist_create(
            user=SpotifyAppUser.get_id(),
            name=playlist_name,
            public=False,
            description=playlist_description,
        )

        playlist_id = playlist["id"]

        added_uris = []
        if track_uris:
            # Add in chunks of 100
            for i in range(0, len(track_uris), 100):
                chunk = track_uris[i:i + 100]
                sp.playlist_add_items(playlist_id, chunk)
                added_uris.extend(chunk)

        return {"playlist_id": playlist_id, "added_tracks": added_uris}
