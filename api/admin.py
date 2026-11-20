from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Comment, Follow, Like, Post, Profile, Save, Story


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "location", "posts_count", "followers_count")
    search_fields = ("name", "user__username", "bio", "location")
    list_filter = ("location",)
    raw_id_fields = ("user",)

    def posts_count(self, obj):
        return obj.posts.count()

    posts_count.short_description = "Posts"

    def followers_count(self, obj):
        return obj.followers_set.count()

    followers_count.short_description = "Followers"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "caption_short", "location", "likes_count", "created_at")
    search_fields = ("caption", "location", "profile__name", "profile__user__username")
    list_filter = ("created_at",)
    raw_id_fields = ("profile",)
    date_hierarchy = "created_at"

    def caption_short(self, obj):
        return (obj.caption or "")[:60]

    caption_short.short_description = "Caption"

    def likes_count(self, obj):
        return obj.likes.count()

    likes_count.short_description = "Likes"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "profile", "text_short", "created_at")
    search_fields = ("text", "profile__name")
    raw_id_fields = ("post", "profile")
    date_hierarchy = "created_at"

    def text_short(self, obj):
        return (obj.text or "")[:60]

    text_short.short_description = "Text"


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "created_at")
    raw_id_fields = ("profile",)
    date_hierarchy = "created_at"


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "following")
    raw_id_fields = ("follower", "following")
    search_fields = ("follower__name", "following__name")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "profile")
    raw_id_fields = ("post", "profile")


@admin.register(Save)
class SaveAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "profile")
    raw_id_fields = ("post", "profile")


# Replace default User admin so Profile shows inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.site_header = "SocialR Admin"
admin.site.site_title = "SocialR"
admin.site.index_title = "Dashboard"
