import cv2
import numpy as np
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from recommendations.emotion import EmotionError, LABELS, predict, preprocess_face


class EmotionPreprocessingTests(SimpleTestCase):
    def test_invalid_bytes_are_rejected(self):
        with self.assertRaisesRegex(EmotionError, "could not be read"):
            preprocess_face(b"not an image")

    def test_image_without_face_is_rejected(self):
        blank = np.zeros((150, 150, 3), dtype=np.uint8)
        ok, encoded = cv2.imencode(".jpg", blank)
        self.assertTrue(ok)
        with self.assertRaisesRegex(EmotionError, "No face"):
            preprocess_face(encoded.tobytes())

    def test_labels_match_fer2013_order(self):
        self.assertEqual(LABELS, ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"])


class EmotionPredictionTests(SimpleTestCase):
    @override_settings(EMOTION_CONFIDENCE_THRESHOLD=0.45)
    def test_low_confidence_is_not_returned_as_a_mood(self):
        from unittest.mock import patch
        face = np.zeros((1, 48, 48, 1), dtype="float32")
        class Model:
            def predict(self, image, verbose=0):
                return np.array([[0.20, 0.10, 0.12, 0.18, 0.14, 0.13, 0.13]])
        with patch("recommendations.emotion.preprocess_face", return_value=face), patch("recommendations.emotion.load_model", return_value=Model()):
            result = predict(b"image")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "low_confidence")


class EmotionEndpointTests(SimpleTestCase):
    def test_missing_image_returns_bad_request(self):
        response = self.client.post(reverse("emotion_predict"))
        self.assertEqual(response.status_code, 400)

    def test_unsupported_upload_returns_unsupported_media_type(self):
        upload = SimpleUploadedFile("note.txt", b"not an image", content_type="text/plain")
        response = self.client.post(reverse("emotion_predict"), {"image": upload})
        self.assertEqual(response.status_code, 415)

    def test_success_response_includes_mapped_mood(self):
        from unittest.mock import patch
        upload = SimpleUploadedFile("face.jpg", b"image bytes", content_type="image/jpeg")
        with patch("recommendations.views.predict", return_value={"ok": True, "emotion": "happy", "confidence": 0.88}):
            response = self.client.post(reverse("emotion_predict"), {"image": upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["emotion"], "happy")
        self.assertEqual(response.json()["music_mood"], "Feel-good")
