from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"), path("dashboard/", views.dashboard, name="dashboard"),
    path("discover/", views.discover, name="discover"), path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"), path("logout/", views.logout_view, name="logout"),
    path("favorites/", views.favorites, name="favorites"), path("favorites/add/", views.favorite_create, name="favorite_create"),
    path("favorites/<int:favorite_id>/delete/", views.favorite_delete, name="favorite_delete"),
    path("history/", views.mood_history, name="history"), path("history/clear/", views.clear_history, name="clear_history"),
    path("privacy/", views.privacy, name="privacy"), path("about/", views.about, name="about"), path("settings/", views.settings_page, name="settings"),
    path("spotify/login/", views.spotify_login, name="spotify_login"), path("spotify/callback/", views.spotify_callback, name="spotify_callback"),
    path("api/health/", views.health, name="health"), path("api/emotion/predict/", views.emotion_predict, name="emotion_predict"),
    path("api/music/search/", views.music_search, name="music_search"), path("api/music/recommendations/", views.recommendations, name="recommendations"),
    path("api/music/track/<str:track_id>/", views.track_detail, name="track_detail"),
    path("api/favorites/", views.favorites_api, name="favorites_api"),
    path("api/mood-history/", views.mood_history_api, name="mood_history_api"),
]
