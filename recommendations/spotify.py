import base64
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


class SpotifyError(Exception):
    pass


_token_cache = {"value": "", "expires": 0}


def _request(url, data=None, headers=None, method=None):
    request = Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        if error.code == 429:
            raise SpotifyError("Spotify is rate limiting requests. Please wait a moment and retry.") from error
        if error.code in (401, 403):
            raise SpotifyError("Spotify declined this request. Check the app's access and development-mode requirements.") from error
        raise SpotifyError(f"Spotify returned an error ({error.code}). {detail}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise SpotifyError("Spotify could not be reached. Check the internet connection and retry.") from error


def _app_token():
    now = time.time()
    if _token_cache["value"] and now < _token_cache["expires"] - 30:
        return _token_cache["value"]
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        raise SpotifyError("Live Spotify search is not configured yet. Add Spotify credentials in the server environment.")
    credentials = base64.b64encode(f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()).decode()
    body = urlencode({"grant_type": "client_credentials"}).encode()
    payload = _request("https://accounts.spotify.com/api/token", body, {"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"})
    _token_cache.update(value=payload["access_token"], expires=now + int(payload.get("expires_in", 3600)))
    return _token_cache["value"]


def search_tracks(query, limit=10):
    params = urlencode({"q": query, "type": "track", "limit": min(max(int(limit), 1), 10), "market": settings.SPOTIFY_MARKET})
    payload = _request(f"https://api.spotify.com/v1/search?{params}", headers={"Authorization": f"Bearer {_app_token()}"})
    tracks = []
    for track in payload.get("tracks", {}).get("items", []):
        images = track.get("album", {}).get("images", [])
        tracks.append({
            "id": track.get("id"), "name": track.get("name", "Unknown track"),
            "artists": ", ".join(a.get("name", "") for a in track.get("artists", [])),
            "album": track.get("album", {}).get("name", ""),
            "image": images[0].get("url", "") if images else "",
            "spotify_url": track.get("external_urls", {}).get("spotify", ""),
            "duration_ms": track.get("duration_ms"), "preview_url": track.get("preview_url"),
        })
    return tracks


def exchange_authorization_code(code):
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        raise SpotifyError("Spotify credentials are not configured on the server.")
    credentials = base64.b64encode(f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()).decode()
    body = urlencode({"grant_type": "authorization_code", "code": code, "redirect_uri": settings.SPOTIFY_REDIRECT_URI}).encode()
    return _request("https://accounts.spotify.com/api/token", body, {"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"})


def spotify_profile(access_token):
    return _request("https://api.spotify.com/v1/me", headers={"Authorization": f"Bearer {access_token}"})


def get_track(track_id):
    if not track_id.isalnum() or len(track_id) != 22:
        return None
    track = _request(f"https://api.spotify.com/v1/tracks/{track_id}?market={settings.SPOTIFY_MARKET}", headers={"Authorization": f"Bearer {_app_token()}"})
    images = track.get("album", {}).get("images", [])
    return {
        "id": track.get("id"), "name": track.get("name", "Unknown track"),
        "artists": ", ".join(a.get("name", "") for a in track.get("artists", [])),
        "album": track.get("album", {}).get("name", ""),
        "image": images[0].get("url", "") if images else "",
        "spotify_url": track.get("external_urls", {}).get("spotify", ""),
        "duration_ms": track.get("duration_ms"), "preview_url": track.get("preview_url"),
    }
