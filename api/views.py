import json
import re
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import Comment, Follow, Like, Post, Profile, Save, Story


# ---------- helpers ----------
def body(request):
    try:
        return json.loads(request.body or "{}")
    except ValueError:
        return {}


def error(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def auth_required(fn):
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error("Please log in.", 401)
        return fn(request, *args, **kwargs)
    return wrapper


def mine(request):
    return Profile.objects.get_or_create(user=request.user, defaults={"name": request.user.username})[0]


def profile_json(p, viewer=None):
    return {
        "id": p.id, "name": p.name, "handle": p.user.username, "bio": p.bio,
        "avatar": p.avatar.url if p.avatar else "",
        "posts": p.posts.count(),
        "followers": p.followers_set.count(),
        "following": p.following_set.count(),
        "isFollowing": bool(viewer and viewer.id != p.id and
                            Follow.objects.filter(follower=viewer, following=p).exists()),
    }


def post_json(p, viewer):
    return {
        "id": p.id,
        "profile": profile_json(p.profile, viewer),
        "isMine": p.profile_id == viewer.id,
        "location": p.location or p.profile.location,
        "image": p.image.url if p.image else "",
        "caption": p.caption,
        "likes": p.likes.count(),
        "liked": p.likes.filter(profile=viewer).exists(),
        "saved": p.saves.filter(profile=viewer).exists(),
        "comments": [{"name": c.profile.name, "text": c.text} for c in p.comments.select_related("profile")],
        "createdAt": p.created_at.isoformat(),
    }


def page(name):
    return FileResponse(open(Path(settings.BASE_DIR) / "public" / name, "rb"), content_type="text/html")


@never_cache
@ensure_csrf_cookie
def index(request):
    if not request.user.is_authenticated:
        return redirect("/login")
    return page("index.html")


@never_cache
@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("/")
    return page("login.html")


# ---------- accounts ----------
@require_POST
def register(request):
    d = body(request)
    username = str(d.get("username", "")).strip().lower()
    password = str(d.get("password", ""))
    name = str(d.get("name", "")).strip() or username
    if not re.fullmatch(r"[a-z0-9_.]{3,30}", username):
        return error("Username must be 3-30 characters: letters, numbers, _ or .")
    if len(password) < 6:
        return error("Password must be at least 6 characters.")
    if User.objects.filter(username=username).exists():
        return error("That username is taken.", 409)
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.create(user=user, name=name[:100])
    login(request, user)
    return JsonResponse({"ok": True})


@require_POST
def login_view(request):
    d = body(request)
    user = authenticate(request, username=str(d.get("username", "")).strip().lower(), password=str(d.get("password", "")))
    if not user:
        return error("Incorrect username or password.")
    login(request, user)
    return JsonResponse({"ok": True})


@require_POST
def logout_view(request):
    logout(request)
    return HttpResponse(status=204)


@auth_required
def me_view(request):
    p = mine(request)
    if request.method == "POST":  # multipart form: name, bio, avatar
        for f in ("name", "bio"):
            if request.POST.get(f) is not None:
                setattr(p, f, request.POST[f][:200])
        if request.FILES.get("avatar"):
            p.avatar = request.FILES["avatar"]
        p.save()
    return JsonResponse(profile_json(p, p))


# ---------- social ----------
@auth_required
def stories(request):
    me = mine(request)
    if request.method == "POST" and request.FILES.get("image"):
        Story.objects.create(profile=me, image=request.FILES["image"])
    others = Profile.objects.filter(stories__isnull=False).exclude(id=me.id).distinct().order_by("id")
    out = []
    for p in [me, *others]:
        out.append({"profile": profile_json(p, me), "isMe": p.id == me.id,
                    "images": [s.image.url for s in p.stories.order_by("id")]})
    return JsonResponse(out, safe=False)


@auth_required
@require_POST
def follow(request, pk):
    me = mine(request)
    target = Profile.objects.filter(pk=pk).first()
    if not target:
        return HttpResponse(status=404)
    if target.id == me.id:
        return error("You can't follow yourself.")
    obj, created = Follow.objects.get_or_create(follower=me, following=target)
    if not created:
        obj.delete()
    return JsonResponse(profile_json(target, me))


@auth_required
def posts(request):
    me = mine(request)
    if request.method == "POST":
        image, caption = request.FILES.get("image"), request.POST.get("caption", "").strip()
        if not image and not caption:
            return error("Add an image or a caption.")
        p = Post.objects.create(profile=me, caption=caption, location=request.POST.get("location", "")[:100])
        if image:
            p.image = image
            p.save()
        return JsonResponse(post_json(p, me))

    qs = Post.objects.select_related("profile__user").annotate(n=Count("likes", distinct=True))
    if request.GET.get("sort") == "top":  # Explore: everyone, most liked first
        qs = qs.order_by("-n", "-id")
    else:  # Feed: you and the people you follow
        ids = list(Follow.objects.filter(follower=me).values_list("following_id", flat=True)) + [me.id]
        qs = qs.filter(profile_id__in=ids).order_by("-id")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(caption__icontains=q) | Q(location__icontains=q) | Q(profile__name__icontains=q) |
                       Q(profile__user__username__icontains=q) | Q(profile__location__icontains=q))
    return JsonResponse([post_json(p, me) for p in qs], safe=False)


def get_post(pk):
    return Post.objects.filter(pk=pk).first()


@auth_required
def post_detail(request, pk):
    me, p = mine(request), get_post(pk)
    if not p:
        return HttpResponse(status=404)
    if request.method == "DELETE":
        if p.profile_id != me.id:
            return error("You can only delete your own posts.", 403)
        p.delete()
        return HttpResponse(status=204)
    return JsonResponse(post_json(p, me))


def toggle(model):
    @auth_required
    @require_POST
    def view(request, pk):
        me, p = mine(request), get_post(pk)
        if not p:
            return HttpResponse(status=404)
        obj, created = model.objects.get_or_create(post=p, profile=me)
        if not created:
            obj.delete()
        return JsonResponse(post_json(p, me))
    return view


like = toggle(Like)
save = toggle(Save)


@auth_required
@require_POST
def comment(request, pk):
    me, p = mine(request), get_post(pk)
    if not p:
        return HttpResponse(status=404)
    text = str(body(request).get("text", "")).strip()
    if text:
        Comment.objects.create(post=p, profile=me, text=text[:500])
    return JsonResponse(post_json(p, me))
