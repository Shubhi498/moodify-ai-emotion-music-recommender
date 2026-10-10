# Spotify setup

1. Sign in to Spotify for Developers and create an app.
2. Add the exact redirect URI configured as `SPOTIFY_REDIRECT_URI` (for example `http://localhost:8000/spotify/callback/`) to the app settings.
3. Copy the Client ID and Client Secret into the server environment only. Never put the Client Secret in HTML, JavaScript, Git, or chat.
4. Set `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`, and a two-letter `SPOTIFY_MARKET`.
5. Restart Django and use search or mood recommendations.

Catalog search uses the Web API Search endpoint and asks for no more than ten tracks in a request. Spotify's February 2026 changes reduced the Search limit to 10 for Development Mode apps and removed a number of endpoints; the application does not depend on Recommendations, Audio Features, Browse categories, or artist top tracks. API errors, missing credentials, no results, missing artwork, absent previews, and rate limits are shown as real conditions.

Current Spotify Development Mode has owner/account eligibility and allowlist limits described in Spotify's developer documentation. A new developer app may not serve an unrestricted public audience. Check the live Developer Dashboard for account eligibility and app quota before publishing the connected integration.

The optional authorization-code sign-in uses OAuth `state` validation. Its token exchange and profile request happen on the Django server; tokens are discarded after the profile check. Catalog search does not require an end user's account login.

The interface opens the actual Spotify track page for full playback. It plays an in-app audio element only when a valid Spotify `preview_url` appears in the Search response; Spotify may return no preview. Full Spotify streaming in an embedded browser player requires the separate Web Playback SDK and an eligible Premium account. That SDK is outside the strict synopsis technology list, so this project does not claim that full playback works inside the page.
