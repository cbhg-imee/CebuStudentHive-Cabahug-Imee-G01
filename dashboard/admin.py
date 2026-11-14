from django.contrib import admin

from .models import Comment, Post, Vote

admin.site.register(Post, list_display=("title", "category", "status", "author", "created_at"), list_filter=("status", "category"))
admin.site.register(Vote)
admin.site.register(Comment)
