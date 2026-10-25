"""
Clip Cup URL Configuration.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import health_check, create_job, get_job, job_history
from .auth_views import auth_register, auth_login, auth_refresh, auth_me, auth_logout

urlpatterns = [
    # Health
    path("api/health", health_check, name="health_check"),

    # Auth endpoints
    path("api/auth/register", auth_register, name="auth_register"),
    path("api/auth/login", auth_login, name="auth_login"),
    path("api/auth/refresh", auth_refresh, name="auth_refresh"),
    path("api/auth/me", auth_me, name="auth_me"),
    path("api/auth/logout", auth_logout, name="auth_logout"),

    # Job endpoints
    path("api/jobs/history", job_history, name="job_history"),  # must come before <job_id>
    path("api/jobs", create_job, name="create_job"),
    path("api/jobs/<str:job_id>", get_job, name="get_job"),
]

# Serve media files locally during development/fallback
if settings.DEBUG:
    media_dir = settings.BASE_DIR / "media"
    urlpatterns += static("/media/", document_root=str(media_dir))
