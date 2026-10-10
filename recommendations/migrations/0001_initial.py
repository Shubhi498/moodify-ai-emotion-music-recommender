import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="FavoriteTrack",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("spotify_id", models.CharField(max_length=64)),
                ("title", models.CharField(max_length=300)),
                ("artists", models.CharField(max_length=500)),
                ("album_art", models.URLField(blank=True)),
                ("spotify_url", models.URLField()),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorite_tracks", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-added_at"], "unique_together": {("user", "spotify_id")} },
        ),
        migrations.CreateModel(
            name="MoodHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("emotion", models.CharField(max_length=32)),
                ("music_mood", models.CharField(max_length=64)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("source", models.CharField(default="manual", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mood_history", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
