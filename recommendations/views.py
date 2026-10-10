import json
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import RequestDataTooBig
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .emotion import EmotionError, predict
from .models import FavoriteTrack, MoodHistory
from .moods import MANUAL_MOODS, MOOD_MAP
from .spotify import SpotifyError, exchange_authorization_code, get_track, search_tracks, spotify_profile


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html", {"moods": MOOD_MAP})


def dashboard(request):
    recent = request.user.mood_history.all()[:5] if request.user.is_authenticated else []
    favorites = request.user.favorite_tracks.all()[:4] if request.user.is_authenticated else []
    return render(request, "dashboard.html", {"moods": MOOD_MAP, "recent": recent, "favorites": favorites})


def discover(request):
    return render(request, "discover.html", {"moods": MOOD_MAP, "manual_moods": MANUAL_MOODS})


def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "auth.html", {"form": form, "title": "Create your account", "button": "Create account"})


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "auth.html", {"form": form, "title": "Welcome back", "button": "Sign in"})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("landing")


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "degraded", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "service": "Moodify AI", "database": "MySQL"})


@require_POST
def emotion_predict(request):
    try:
        upload = request.FILES.get("image")
    except RequestDataTooBig:
        return JsonResponse({"error": f"Image request must be smaller than {settings.MAX_IMAGE_UPLOAD_MB} MB."}, status=413)
    if not upload:
        return JsonResponse({"error": "Choose a webcam image to analyze."}, status=400)
    if upload.size > settings.MAX_IMAGE_UPLOAD_MB * 1024 * 1024:
        return JsonResponse({"error": f"Image must be smaller than {settings.MAX_IMAGE_UPLOAD_MB} MB."}, status=413)
    if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        return JsonResponse({"error": "Upload a JPG, PNG, or WebP image."}, status=415)
    try:
        result = predict(upload.read())
    except EmotionError as error:
        return JsonResponse({"error": str(error)}, status=422)
    if result.get("ok"):
        mood = MOOD_MAP[result["emotion"]]
        result["music_mood"] = mood["label"]
        if request.user.is_authenticated:
            MoodHistory.objects.create(user=request.user, emotion=result["emotion"], music_mood=mood["label"], confidence=result["confidence"], source="camera")
    return JsonResponse(result)


@require_GET
def music_search(request):
    query = request.GET.get("q", "").strip()[:120]
    if not query:
        return JsonResponse({"error": "Enter a song, artist, or mood to search."}, status=400)
    try:
        tracks = search_tracks(query)
    except SpotifyError as error:
        return JsonResponse({"error": str(error), "tracks": []}, status=503)
    return JsonResponse({"tracks": tracks, "source": "Spotify Web API", "count": len(tracks)})


@require_GET
def recommendations(request):
    emotion = request.GET.get("emotion", "").lower()
    mood = request.GET.get("mood", "").lower()
    if emotion in MOOD_MAP:
        query = MOOD_MAP[emotion]["query"]
        label = MOOD_MAP[emotion]["label"]
    elif mood in MANUAL_MOODS:
        query = MANUAL_MOODS[mood]
        label = mood.title()
    else:
        return JsonResponse({"error": "Choose a supported emotion or mood."}, status=400)
    try:
        tracks = search_tracks(query)
    except SpotifyError as error:
        return JsonResponse({"error": str(error), "tracks": []}, status=503)
    if request.user.is_authenticated and not emotion:
        MoodHistory.objects.create(user=request.user, emotion="Manual", music_mood=label, source="manual")
    return JsonResponse({"tracks": tracks, "mood": label, "source": "Spotify Web API", "count": len(tracks)})


@require_GET
def track_detail(request, track_id):
    try:
        track = get_track(track_id)
    except SpotifyError as error:
        return JsonResponse({"error": str(error)}, status=503)
    if not track:
        return JsonResponse({"error": "Track not found."}, status=404)
    return JsonResponse(track)


@require_POST
@login_required
def favorite_create(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    required = ["id", "name", "artists", "spotify_url"]
    if any(not data.get(key) for key in required):
        return JsonResponse({"error": "Track details are incomplete."}, status=400)
    favorite, created = FavoriteTrack.objects.get_or_create(user=request.user, spotify_id=data["id"], defaults={"title": data["name"][:300], "artists": data["artists"][:500], "spotify_url": data["spotify_url"], "album_art": data.get("image", "")})
    return JsonResponse({"ok": True, "created": created, "id": favorite.id}, status=201 if created else 200)


@require_GET
@login_required
def favorites(request):
    return render(request, "favorites.html", {"favorites": request.user.favorite_tracks.all()})


@require_GET
@login_required
def favorites_api(request):
    items = request.user.favorite_tracks.all()
    return JsonResponse({"favorites": [{"id": item.id, "spotify_id": item.spotify_id, "name": item.title, "artists": item.artists, "image": item.album_art, "spotify_url": item.spotify_url} for item in items]})


@require_POST
@login_required
def favorite_delete(request, favorite_id):
    FavoriteTrack.objects.filter(id=favorite_id, user=request.user).delete()
    return redirect("favorites")


@require_GET
@login_required
def mood_history(request):
    return render(request, "history.html", {"history": request.user.mood_history.all()[:100]})


@require_GET
@login_required
def mood_history_api(request):
    items = request.user.mood_history.all()[:100]
    return JsonResponse({"history": [{"emotion": item.emotion, "music_mood": item.music_mood, "confidence": item.confidence, "source": item.source, "created_at": item.created_at.isoformat()} for item in items]})


@require_POST
@login_required
def clear_history(request):
    request.user.mood_history.all().delete()
    messages.success(request, "Your mood history has been cleared.")
    return redirect("history")


def privacy(request):
    return render(request, "info.html", {"title": "Privacy", "body": "Camera access starts only when you choose it. A captured frame is sent for analysis and is not saved. If you sign in, your detected mood label and confidence are stored in your account history; you can clear that history at any time. Spotify credentials remain on the Django server."})


def about(request):
    return render(request, "info.html", {"title": "About Moodify AI", "body": "An academic project exploring emotion-aware music discovery. OpenCV detects a face, a CNN trained on FER-2013 classifies a facial expression, and a configurable mapping turns that estimate into a Spotify catalog search. It is a lightweight expression estimate, not a medical or psychological assessment."})


def settings_page(request):
    return render(request, "info.html", {"title": "Settings", "body": "Moodify AI keeps your facial image only in memory while processing the request. Sign in to save favorites and mood history. You can clear mood history from the Mood History page."})


def spotify_login(request):
    if not settings.SPOTIFY_CLIENT_ID:
        messages.error(request, "Spotify connection is not configured yet.")
        return redirect("discover")
    state = secrets.token_urlsafe(24)
    request.session["spotify_oauth_state"] = state
    params = {"client_id": settings.SPOTIFY_CLIENT_ID, "response_type": "code", "redirect_uri": settings.SPOTIFY_REDIRECT_URI, "state": state, "scope": "user-read-private"}
    return redirect("https://accounts.spotify.com/authorize?" + urlencode(params))


def spotify_callback(request):
    state = request.GET.get("state", "")
    expected = request.session.pop("spotify_oauth_state", "")
    if not expected or not secrets.compare_digest(state, expected):
        messages.error(request, "Spotify sign-in could not be verified. Please try again.")
        return redirect("discover")
    if request.GET.get("error"):
        messages.error(request, "Spotify sign-in was cancelled or declined.")
    else:
        try:
            tokens = exchange_authorization_code(request.GET.get("code", ""))
            profile = spotify_profile(tokens["access_token"])
            request.session["spotify_account"] = profile.get("display_name") or profile.get("id") or "Connected"
            messages.success(request, "Spotify account connected successfully.")
        except (SpotifyError, KeyError) as error:
            messages.error(request, f"Spotify could not complete sign-in: {error}")
    return redirect("discover")
