from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from api.models import Comment, Follow, Like, Post, Profile, Story

PASSWORD = "demo1234"


def art(h):
    """Generated gradient artwork, so the demo works without photo files."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="hsl({h},75%,62%)"/><stop offset="1" stop-color="hsl({(h + 60) % 360},70%,40%)"/>'
        '</linearGradient></defs><rect width="800" height="500" fill="url(#g)"/>'
        f'<circle cx="{150 + h % 300}" cy="170" r="95" fill="#fff" fill-opacity=".25"/>'
        '<circle cx="580" cy="360" r="150" fill="#fff" fill-opacity=".15"/></svg>'
    ).encode()


PEOPLE = [  # username, name, location, caption, hue
    ("sonya", "Sonya Leena", "Dubai, UAE", "You can never dull my sparkle ✨", 190),
    ("adam", "Adam Addisin", "Oklahoma, US", "In photography, there is a reality so subtle that it becomes more real than reality.", 20),
    ("andrew", "Andrew Dewitt", "Overland Park, KS", "The unexpected moment is always sweeter!", 130),
    ("nicole", "Nicole Segall", "New Delhi, India", "Colour outside the lines.", 350),
    ("ashley", "Ashley Rowe", "Austin, TX", "Golden hour never gets old.", 40),
    ("michael", "Michael Gilmore", "Lawrence, KS", "Quiet streets, loud thoughts.", 260),
    ("damian", "Damian Efron", "Birmingham, UK", "Made a new friend today.", 90),
]


def make_user(username, name, location="", bio=""):
    user = User.objects.create_user(username=username, password=PASSWORD)
    return Profile.objects.create(user=user, name=name, location=location, bio=bio)


class Command(BaseCommand):
    help = "Fill the database with demo accounts, stories and posts."

    def handle(self, *args, **opts):
        if Profile.objects.exists():
            self.stdout.write("Database already has data; nothing seeded.")
            return
        me = make_user("abhi", "Abhinav Khare", "Chennai, India", "UI Designer | Traveler | Lifestyle Blogger")
        for h, cap in ((210, "Sketching out the next feature."), (300, "Weekend wandering.")):
            Post.objects.create(profile=me, caption=cap).image.save("art.svg", ContentFile(art(h)))
        others = []
        for username, name, loc, cap, hue in PEOPLE:
            p = make_user(username, name, loc)
            Story.objects.create(profile=p).image.save("story.svg", ContentFile(art((hue + 30) % 360)))
            post = Post.objects.create(profile=p, caption=cap)
            post.image.save("art.svg", ContentFile(art(hue)))
            Comment.objects.create(post=post, profile=me, text="Love this!")
            Follow.objects.create(follower=me, following=p)
            others.append((p, post))
        for i, (p, post) in enumerate(others):
            for liker, _ in others[: i + 2]:
                if liker != p:
                    Like.objects.create(post=post, profile=liker)
            if i < 3:
                Follow.objects.create(follower=p, following=me)
        self.stdout.write(f"Seeded demo data. Log in as 'abhi' (or any of: {', '.join(x[0] for x in PEOPLE)}) with password '{PASSWORD}'.")
