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
        self.client.post(reverse("dashboard:submit"), {"title": "Study Spot", "category": "STUDY", "body": "A useful study spot", "location_tag": "X"})
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
        self.assertContains(self.client.get(reverse("dashboard:home")), "Study Spot")


class SubmissionCrudTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner@example.com", PW)
        self.other = User.objects.create_user("other@example.com", PW)
        self.admin = User.objects.create_user("admin@example.com", PW, role=User.Role.ADMIN)
        self.post = Post.objects.create(author=self.owner, title="Study cafe", body="Quiet place to study", category="STUDY")

    def test_student_can_list_and_edit_own_pending_post(self):
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse("dashboard:my_submissions")), "Study cafe")
        response = self.client.post(reverse("dashboard:edit_submission", args=[self.post.pk]), {
            "title": "Updated cafe", "body": "Updated quiet study spot", "category": "STUDY", "location_tag": "Cebu"
        })
        self.assertRedirects(response, reverse("dashboard:my_submissions"))
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated cafe")
        self.assertEqual(self.post.status, Post.Status.PENDING)

    def test_student_cannot_modify_someone_elses_post(self):
        self.client.force_login(self.other)
        for name in ("dashboard:edit_submission", "dashboard:delete_submission"):
            self.assertEqual(self.client.get(reverse(name, args=[self.post.pk])).status_code, 404)
            self.assertEqual(self.client.post(reverse(name, args=[self.post.pk]), {}).status_code, 404)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_approved_post_is_locked(self):
        self.post.status = Post.Status.APPROVED
        self.post.save(update_fields=["status"])
        self.client.force_login(self.owner)
        for name in ("dashboard:edit_submission", "dashboard:delete_submission"):
            self.assertEqual(self.client.get(reverse(name, args=[self.post.pk])).status_code, 404)

    def test_delete_requires_post(self):
        self.client.force_login(self.owner)
        url = reverse("dashboard:delete_submission", args=[self.post.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
        self.assertRedirects(self.client.post(url), reverse("dashboard:my_submissions"))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_admin_cannot_use_student_crud(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("dashboard:my_submissions")).status_code, 403)
        self.assertEqual(self.client.post(reverse("dashboard:submit"), {}).status_code, 403)

    def test_validation_rejects_short_or_whitespace_fields(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("dashboard:submit"), {"title": " a ", "body": "   ", "category": "STUDY"})
        self.assertEqual(Post.objects.count(), 1)
