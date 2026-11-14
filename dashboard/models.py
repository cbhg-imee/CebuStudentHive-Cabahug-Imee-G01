from django.conf import settings
from django.db import models


class Post(models.Model):
    class Category(models.TextChoices):
        DISCOUNT = "DISCOUNT", "Student Discounts"
        STUDY = "STUDY", "Study Spots"
        EVENT = "EVENT", "Campus Events"
        SCHOLARSHIP = "SCHOLARSHIP", "Scholarships"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    FLAIRS = {"DISCOUNT": "text-bg-success", "STUDY": "text-bg-info", "EVENT": "text-bg-primary", "SCHOLARSHIP": "text-bg-warning"}

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200)
    body = models.TextField(max_length=2000)
    category = models.CharField(max_length=12, choices=Category.choices)
    location_tag = models.CharField("merchant or campus", max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def flair_class(self):
        return self.FLAIRS.get(self.category, "text-bg-secondary")

    def __str__(self):
        return self.title


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="votes")
    value = models.SmallIntegerField(choices=[(1, "Up"), (-1, "Down")])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_vote_per_user_post")]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
