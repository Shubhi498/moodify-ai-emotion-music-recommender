import json
from unittest.mock import patch

import numpy as np
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from recommendations.models import FavoriteTrack, MoodHistory
from recommendations.spotify import SpotifyError


class PublicApiTests(TestCase):
    def test_health_reports_running_service(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_emotion_endpoint_requires_image(self):
        response = self.client.post(reverse("emotion_predict"))
        self.assertEqual(response.status_code, 400)

    def test_emotion_endpoint_rejects_unsupported_upload(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        response = self.client.post(reverse("emotion_predict"), {"image": SimpleUploadedFile("bad.txt", b"data", content_type="text/plain")})
        self.assertEqual(response.status_code, 415)

    @patch("recommendations.views.predict", return_value={"ok": True, "emotion": "happy", "confidence": 0.88})
    def test_prediction_maps_emotion_without_saving_image(self, _predict):
        from django.core.files.uploadedfile import SimpleUploadedFile
        response = self.client.post(reverse("emotion_predict"), {"image": SimpleUploadedFile("face.jpg", b"frame", content_type="image/jpeg")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["music_mood"], "Feel-good")
        self.assertEqual(MoodHistory.objects.count(), 0)

    def test_invalid_recommendation_mood_is_rejected(self):
        response = self.client.get(reverse("recommendations"), {"mood": "unknown"})
        self.assertEqual(response.status_code, 400)

    @patch("recommendations.views.search_tracks", side_effect=SpotifyError("offline"))
    def test_spotify_failure_is_reported_clearly(self, _search):
        response = self.client.get(reverse("music_search"), {"q": "jazz"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("offline", response.json()["error"])


class AccountApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="listener", password="A-long-password-23")

    def test_favorites_require_login(self):
        self.client.logout()
        response = self.client.get(reverse("favorites"))
        self.assertEqual(response.status_code, 302)

    def test_favorite_can_be_saved_and_deleted(self):
        self.client.force_login(self.user)
        payload = {"id": "abc123", "name": "Night Drive", "artists": "Example Artist", "spotify_url": "https://open.spotify.com/track/abc123", "image": ""}
        response = self.client.post(reverse("favorite_create"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FavoriteTrack.objects.get().user, self.user)
        delete_response = self.client.post(reverse("favorite_delete", args=[FavoriteTrack.objects.get().id]))
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(FavoriteTrack.objects.count(), 0)

    def test_user_can_clear_mood_history(self):
        self.client.force_login(self.user)
        MoodHistory.objects.create(user=self.user, emotion="happy", music_mood="Feel-good")
        response = self.client.post(reverse("clear_history"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MoodHistory.objects.count(), 0)
