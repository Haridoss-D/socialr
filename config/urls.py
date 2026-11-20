from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from api import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index),
    path("login", views.login_page),
    path("api/register", views.register),
    path("api/login", views.login_view),
    path("api/logout", views.logout_view),
    path("api/me", views.me_view),
    path("api/stories", views.stories),
    path("api/profiles/<int:pk>/follow", views.follow),
    path("api/posts", views.posts),
    path("api/posts/<int:pk>", views.post_detail),
    path("api/posts/<int:pk>/like", views.like),
    path("api/posts/<int:pk>/save", views.save),
    path("api/posts/<int:pk>/comments", views.comment),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
