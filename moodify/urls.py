from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [path("admin/", admin.site.urls), path("", include("recommendations.urls"))]

# Keep the template app self-contained on simple Django hosts that do not offer
# a separate static-file server. collectstatic populates STATIC_ROOT at release.
if not settings.DEBUG:
    urlpatterns.append(re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}))
