from functools import lru_cache

import cv2
import numpy as np
from django.conf import settings

LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


class EmotionError(Exception):
    pass


def preprocess_face(image_bytes):
    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if frame is None:
        raise EmotionError("This image could not be read. Choose a valid JPG or PNG image.")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
    if len(faces) == 0:
        raise EmotionError("No face was found. Face the camera with clear, even lighting and try again.")
    x, y, width, height = max(faces, key=lambda item: item[2] * item[3])
    crop = gray[y:y + height, x:x + width]
    crop = cv2.resize(crop, (48, 48), interpolation=cv2.INTER_AREA)
    normalized = crop.astype("float32") / 255.0
    return normalized.reshape(1, 48, 48, 1)


@lru_cache(maxsize=1)
def load_model():
    path = settings.EMOTION_MODEL_PATH
    if not path.exists():
        raise EmotionError("The emotion model is not installed. Follow the FER-2013 training steps in the README.")
    try:
        from tensorflow.keras.models import load_model as keras_load_model
        return keras_load_model(path)
    except Exception as error:
        raise EmotionError("The emotion model could not be loaded. Check its file and TensorFlow installation.") from error


def predict(image_bytes):
    face = preprocess_face(image_bytes)
    scores = load_model().predict(face, verbose=0)[0]
    index = int(np.argmax(scores))
    confidence = float(scores[index])
    if confidence < settings.EMOTION_CONFIDENCE_THRESHOLD:
        return {"ok": False, "reason": "low_confidence", "confidence": confidence, "message": "The expression is unclear. Try again or choose a mood manually."}
    return {"ok": True, "emotion": LABELS[index], "confidence": confidence}
