# Deployment notes

This project requires Django, a reachable MySQL server, a trained CNN weight file, HTTPS for webcam access, and outbound HTTPS requests to Spotify. Production uses the approved Gunicorn WSGI server via the root `Procfile` and serves static files over HTTPS.

Deployment is not configured to use SQLite or PostgreSQL. The `settings.py` database engine remains MySQL. Copy every variable in `.env.example` to the host's private environment settings. Set `DJANGO_DEBUG=False`, a newly generated secret, a precise `DJANGO_ALLOWED_HOSTS`, HTTPS `DJANGO_CSRF_TRUSTED_ORIGINS`, database credentials, Spotify credentials and redirect URI, and the model path. Run migrations, collect static files, and set the host's static-files mapping. Then verify `/api/health/`, account flows, image prediction with the installed model, and Spotify search using a fresh browser session.

## Hosting target and limits

The `Procfile` collects static assets and starts the Django application with Gunicorn bound to the host-provided `PORT`. Do not use Django's development server for public hosting. The synopsis does not specify a deployment provider; Railway is a candidate because it supports Python application services and MySQL services. Connect its MySQL service values to the `MYSQL_*` environment variables in `.env.example`, and set `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, Spotify credentials, and `EMOTION_MODEL_PATH` in the private service settings. With no additional static-serving technology allowed, Django serves the collected assets directly as a small-deployment fallback; this is less efficient than a dedicated static server at larger scale.

Use Railway's deployment documentation to link a GitHub repository, create the Python service, provision MySQL, and configure environment variables. The service must have enough memory for TensorFlow and the actual CNN weights. Store the model file in a persistent location or include it as a reviewed deployment artifact; the source repository intentionally excludes trained weights and FER-2013 data. Set up HTTPS before testing browser camera access.

Railway's current pricing page describes a usage-based Hobby plan with a $5/month minimum charge, with additional usage charged separately. Review current pricing before creating resources; this repository does not provision paid hosting. GitHub login, Railway account setup, model weights, a running MySQL service, and Spotify developer credentials are still needed to complete and verify a live deployment.

## Release checklist

1. Link this repository to the host and deploy using the `Procfile`.
2. Set all production environment variables; keep secrets in the provider's private settings.
3. Provision MySQL, map its connection settings to the `MYSQL_*` variables, and run `python manage.py migrate`.
4. Run `python manage.py collectstatic --noinput` if the host's build/release command requires it, and configure static serving according to the provider.
5. Add real, evaluated CNN weights and set `EMOTION_MODEL_PATH` to their location.
6. Set Spotify's exact deployed callback URL and `SPOTIFY_REDIRECT_URI` to match.
7. Verify the health endpoint, login, manual mood search, camera permission-denied path, face/no-face inference, Spotify search, and mobile layout using the deployed URL.

Public GitHub publication and live deployment still require the user's GitHub and hosting account authorization. Do not commit environment files or model weights.
