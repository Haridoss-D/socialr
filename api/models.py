from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    bio = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar = models.FileField(upload_to="avatars/", blank=True)


class Follow(models.Model):
    follower = models.ForeignKey(Profile, related_name="following_set", on_delete=models.CASCADE)
    following = models.ForeignKey(Profile, related_name="followers_set", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("follower", "following")


class Post(models.Model):
    profile = models.ForeignKey(Profile, related_name="posts", on_delete=models.CASCADE)
    image = models.FileField(upload_to="posts/", blank=True)
    caption = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("post", "profile")


class Save(models.Model):
    post = models.ForeignKey(Post, related_name="saves", on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("post", "profile")


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Story(models.Model):
    profile = models.ForeignKey(Profile, related_name="stories", on_delete=models.CASCADE)
    image = models.FileField(upload_to="stories/")
    created_at = models.DateTimeField(auto_now_add=True)
