from django.test import TestCase
from django.urls import reverse

from .models import User

PW = "S3curePass!xyz"


class AuthFlowTests(TestCase):
    def test_signup_creates_hashed_student(self):
        r = self.client.post(reverse("accounts:signup"), {
            "email": "A@Example.com", "first_name": "Ana", "last_name": "Reyes",
            "password1": PW, "password2": PW})
        self.assertRedirects(r, reverse("accounts:login"))
        u = User.objects.get(email="a@example.com")
        self.assertEqual(u.role, User.Role.STUDENT)
        self.assertNotEqual(u.password, PW)
        self.assertTrue(u.check_password(PW))

    def test_signup_rejects_duplicate_email_and_mismatch(self):
        User.objects.create_user("a@example.com", PW)
        r = self.client.post(reverse("accounts:signup"), {
            "email": "a@example.com", "first_name": "A", "last_name": "B",
            "password1": PW, "password2": "different"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("email", r.context["form"].errors)
        self.assertIn("password2", r.context["form"].errors)

    def test_login_redirects_by_role(self):
        User.objects.create_user("s@example.com", PW)
        User.objects.create_user("m@example.com", PW, role=User.Role.ADMIN)
        r = self.client.post(reverse("accounts:login"), {"username": "s@example.com", "password": PW})
        self.assertRedirects(r, reverse("dashboard:home"))
        self.client.post(reverse("accounts:logout"))
        r = self.client.post(reverse("accounts:login"), {"username": "m@example.com", "password": PW})
        self.assertRedirects(r, reverse("dashboard:admin_panel"))

    def test_bad_login_shows_error(self):
        r = self.client.post(reverse("accounts:login"), {"username": "x@example.com", "password": "nope"})
        self.assertContains(r, "Incorrect email or password")

    def test_logout_requires_post(self):
        User.objects.create_user("s@example.com", PW)
        self.client.login(username="s@example.com", password=PW)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)

    def test_profile_requires_login_and_is_own_only(self):
        r = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(r, "/accounts/login/?next=/accounts/profile/")
        u = User.objects.create_user("s@example.com", PW)
        User.objects.create_user("o@example.com", PW)
        self.client.force_login(u)
        r = self.client.get(reverse("accounts:profile"))
        self.assertEqual(r.context["object"], u)
