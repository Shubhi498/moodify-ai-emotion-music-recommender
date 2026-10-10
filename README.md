# Moodify AI

Emotion-Based Music Recommendation System Using AI — a Django and MySQL academic project that estimates a facial expression with an OpenCV face detector and FER-2013 CNN, maps the result to a music mood, and searches Spotify's catalog.

## What works in this repository

- Django-rendered responsive landing, dashboard, discovery, sign-in, favorites, mood history, privacy, settings, and about pages.
- Explicit browser camera start, stop, and capture controls; manual mood selection works without a camera.
- Validated OpenCV face crop and TensorFlow/Keras seven-class CNN inference endpoint with a configurable low-confidence fallback. Recognition requires locally trained FER-2013 weights; none are included or claimed to be trained.
- Django session authentication; MySQL persistence for favorites and mood history; history clearing.
- Server-side Spotify catalog search using real API results when credentials are configured; OAuth authorization-code callback with state validation.
- Bottom preview player plays only returned Spotify preview URLs. Full-track playback opens the Spotify track page.
- Tests and GitHub Actions configured to use MySQL.

## Synopsis stack

Python, Django, HTML, CSS, JavaScript, MySQL, TensorFlow/Keras, CNN, OpenCV, NumPy, Spotify Web API, VS Code, and GitHub. No frontend framework or UI package is used.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the system flow and modules, [docs/model.md](docs/model.md) for training and preprocessing, [docs/spotify.md](docs/spotify.md) for Spotify configuration and current API boundaries, and [docs/deployment.md](docs/deployment.md) for production requirements.

## Local setup

Requirements: Python compatible with the listed packages, MySQL Server, and a modern browser. On Windows, install a compatible MySQL client build tool if needed by `mysqlclient`. TensorFlow package/platform support differs by operating system; use a runtime supported by the selected TensorFlow release.

1. Create a MySQL database and user with UTF-8 support, then grant the user access to that database.
2. Create and activate a Python virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and set the secret and MySQL values. The Django development server does not load `.env` automatically: set environment variables in your shell or IDE run configuration.
5. Set `DJANGO_SECRET_KEY`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, and `MYSQL_PORT` in that environment.
6. Run `python manage.py migrate` and `python manage.py runserver`.
7. Open `http://127.0.0.1:8000/`. Webcam access is allowed on localhost; production camera access needs HTTPS.

The project intentionally has no SQLite fallback. A reachable MySQL service is required for Django checks, migrations, sessions, accounts, favorites, and mood history.

## FER-2013 model

Obtain the FER-2013 CSV from its dataset source and follow [docs/model.md](docs/model.md). Train with:

```text
python ai_model/train_fer2013.py C:\path\to\fer2013.csv --epochs 35
```

The script evaluates only the dataset's PrivateTest split and prints metrics from that run. Its `.keras` output is ignored by Git. Until a real model file exists at `ai_model/models/emotion_cnn.keras` (or `EMOTION_MODEL_PATH`), the prediction endpoint reports that model weights are unavailable; it never invents a successful prediction.

## Spotify configuration

Create an app in Spotify for Developers, allow the exact redirect URI, and set `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`, and `SPOTIFY_MARKET`. Keep the client secret on the Django server only. See [docs/spotify.md](docs/spotify.md) for up-to-date endpoint constraints, development-mode limits, OAuth behavior, and playback limits.

Search and mood discovery call Spotify. If credentials are absent, the site displays a configuration error instead of fabricated demo tracks. Spotify can omit album art or preview URLs. The player then offers the real Spotify track link and does not claim it is playing. Full embedded Spotify playback is not implemented because its separate SDK is not among the strict allowed technologies.

## API

- `GET /api/health/`
- `POST /api/emotion/predict/` — multipart `image` (JPG, PNG, or WebP; size limit configured in Django settings).
- `GET /api/music/search/?q=...`
- `GET /api/music/recommendations/?emotion=happy` or `?mood=chill`
- `GET /api/music/track/<spotify-id>/`
- `POST /favorites/add/` (authenticated JSON)
- `GET /favorites/` and `GET /history/` (authenticated)
- `GET /api/favorites/` and `GET /api/mood-history/` (authenticated JSON)
- `POST /history/clear/` (authenticated)
- `GET /spotify/login/` and `GET /spotify/callback/`

The API returns HTTP 400 for invalid inputs, 413 for oversized images, 415 for unsupported uploads, 422 for image/face/model inference errors, 503 for Spotify failures, and 404 for missing tracks.

## Tests

Tests use Django's test runner and the configured MySQL database; there is no test-only SQLite substitution. With MySQL running and environment variables set, run:

```text
python manage.py check
python manage.py migrate
python manage.py test
```

The suite covers image validation and no-face handling, preprocessing labels, low-confidence responses, health and emotion API validation, Spotify errors, authentication, favorite create/delete, and mood-history deletion. No local test result is claimed until these commands have been run successfully in an environment with the dependencies and MySQL available.

## Privacy

The camera is opt-in. A single captured frame is sent to the Django server for in-memory processing and is not stored. Authenticated users' emotion/mood labels and confidence values are stored in MySQL as mood history and can be deleted from the history page. See the in-app Privacy page.

## Deployment status and limitations

This source tree includes a Gunicorn production start command, approved as the WSGI server for deployment. It has not been published to GitHub or deployed. Production still requires MySQL hosting, HTTPS, actual CNN weights, Spotify credentials, and GitHub/hosting account access. Railway is documented as a candidate host; review its usage-based pricing (currently a $5/month Hobby minimum) before provisioning it. See [docs/deployment.md](docs/deployment.md). Spotify Development Mode may limit app owners and allowlisted users, and preview/full playback availability is not guaranteed.

## License

No license is declared. Add a license only after the project owners choose its terms.
