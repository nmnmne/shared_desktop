"""shared desktop URL configuration."""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", include("tools.urls", namespace="tools")),
    path("index/", include("board.urls")),
    path("prog/", include("prog.urls")),
    path("tools/", include("tools.urls", namespace="tools_root")),
    path("admin/", admin.site.urls),
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
    path(r'api/v1/auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]

handler403 = 'board.views.handler403'
handler404 = 'board.views.handler404'
handler500 = 'board.views.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
