# Architecture

## Required project stack

This implementation follows synopsis sections 5.2 and 7: Python and Django, HTML/CSS/JavaScript, MySQL, OpenCV, TensorFlow/Keras, NumPy, and the Spotify Web API. The browser Media Capture API is used for the webcam, as specified in section 7.4. No UI framework or JavaScript package is used.

## Request flow

1. The user opens the Django-rendered dashboard or discovery page.
2. A camera stream starts only after the user selects **Start camera**. The browser captures one frame only after **Capture & analyze**.
3. The image travels to `POST /api/emotion/predict/`. Django validates its type and size. OpenCV decodes the frame, locates the largest face with its Haar Cascade, converts it to grayscale, crops and resizes it to 48 by 48 pixels, and normalizes pixels to `[0, 1]`.
4. TensorFlow/Keras loads the local seven-class FER-2013 CNN. A confidence below the configured threshold is returned as a retry response instead of a confident mood.
5. The user may accept the suggested mapped vibe or choose a different mood. The Django view converts it into a catalog query.
6. Django calls Spotify Search for up to ten current catalog tracks. Album art, title, artists, Spotify links, and preview URLs are shown only when Spotify returns them.
7. Django sessions use the MySQL database. Mood labels/confidence and favorites are associated with authenticated Django users; facial images are not saved.

## Django modules

- `moodify`: settings, URL routing, and WSGI entry point.
- `recommendations`: models, pages, validation, emotion pipeline, mood mapping, and Spotify client.
- `templates`: Django-rendered user interface.
- `static`: project CSS and vanilla JavaScript, including camera and preview controls.
- `ai_model/train_fer2013.py`: reproducible FER-2013 training and evaluation.
- `tests`: Django tests for image handling, low-confidence responses, API validation, Spotify failures, authentication, favorites, and history deletion.

## Spotify boundaries

Catalog search is performed server-side using Spotify's Client Credentials flow, so the client secret never reaches the browser. An optional authorization-code callback validates the OAuth `state`, exchanges the code server-side, retrieves the authorized profile, and retains no access or refresh token. Full playback via the Spotify Web Playback SDK is intentionally not included: the synopsis lists the Web API, and the strict technology constraint asks that no unlisted technology be introduced. The bottom player plays only a real preview URL if Spotify returns one. Otherwise it clearly says the preview is unavailable and offers the Spotify track link.
