from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Post, Vote

PW = "S3curePass!xyz"


class RoleGuardTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("s@example.com", PW)
        self.admin = User.objects.create_user("m@example.com", PW, role=User.Role.ADMIN)

    def test_anonymous_redirected_to_login(self):
        for name in ("dashboard:home", "dashboard:admin_panel"):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302)
            self.assertTrue(r.url.startswith("/accounts/login/"))

    def test_student_blocked_from_admin_with_403_template(self):
        self.client.force_login(self.student)
        r = self.client.get(reverse("dashboard:admin_panel"))
        self.assertEqual(r.status_code, 403)
        self.assertTemplateUsed(r, "403.html")
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 200)

    def test_admin_blocked_from_student_feed(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 403)
        self.assertEqual(self.client.get(reverse("dashboard:admin_panel")).status_code, 200)

    def test_submit_moderate_vote_flow(self):
        self.client.force_login(self.student)
        self.client.post(reverse("dashboard:submit"), {"title": "T", "category": "STUDY", "body": "B", "location_tag": "X"})
        post = Post.objects.get()
        self.assertEqual(post.status, Post.Status.PENDING)
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(reverse("dashboard:moderate", args=[post.pk, "approve"])).status_code, 403)
        self.client.force_login(self.admin)
        self.client.post(reverse("dashboard:moderate", args=[post.pk, "approve"]))
        post.refresh_from_db()
        self.assertEqual(post.status, Post.Status.APPROVED)
        self.client.force_login(self.student)
        r = self.client.post(reverse("dashboard:vote", args=[post.pk]), {"value": 1})
        self.assertEqual(r.json(), {"score": 1, "user_vote": 1})
        r = self.client.post(reverse("dashboard:vote", args=[post.pk]), {"value": 1})
        self.assertEqual(r.json(), {"score": 0, "user_vote": 0})
        self.assertEqual(Vote.objects.count(), 0)
        self.assertContains(self.client.get(reverse("dashboard:home")), "T")
