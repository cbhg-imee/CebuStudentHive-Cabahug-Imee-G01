from django.core.management.base import BaseCommand

from accounts.models import User
from dashboard.models import Comment, Post

SAMPLES = [
    ("DISCOUNT", "Student discount with school ID (sample)", "Colon Street area", "Sample entry for demo purposes. Replace with real, peer-verified discounts."),
    ("STUDY", "Quiet reading hall (sample)", "Cebu City", "Sample entry for demo purposes. Describe noise level, outlets, Wi-Fi, and hours."),
    ("EVENT", "Campus workshop on résumé writing (sample)", "USC Talamban", "Sample entry for demo purposes. Add date, venue, and registration link."),
    ("SCHOLARSHIP", "Scholarship application window (sample)", "Cebu-wide", "Sample entry for demo purposes. Add eligibility and deadline."),
]


class Command(BaseCommand):
    help = "Create a demo student and a few clearly-labelled sample posts. Development only."

    def handle(self, *args, **opts):
        user, created = User.objects.get_or_create(email="demo.student@example.com", defaults={"first_name": "Demo", "last_name": "Student", "university": "Sample University"})
        if created:
            user.set_password("DemoStudent!2026")
            user.save()
        for cat, title, tag, body in SAMPLES:
            post, new = Post.objects.get_or_create(title=title, defaults={"author": user, "category": cat, "location_tag": tag, "body": body, "status": Post.Status.APPROVED})
            if new:
                Comment.objects.create(post=post, author=user, body="Sample comment. Verify before you rely on this.")
        self.stdout.write(self.style.SUCCESS("Seeded. Demo login: demo.student@example.com / DemoStudent!2026"))
