from django.conf import settings
from django.db import models


class FavoriteTrack(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_tracks")
    spotify_id = models.CharField(max_length=64)
    title = models.CharField(max_length=300)
    artists = models.CharField(max_length=500)
    album_art = models.URLField(blank=True)
    spotify_url = models.URLField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "spotify_id")
        ordering = ["-added_at"]


class MoodHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mood_history")
    emotion = models.CharField(max_length=32)
    music_mood = models.CharField(max_length=64)
    confidence = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=16, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
