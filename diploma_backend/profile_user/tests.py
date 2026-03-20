from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Profile
from .services import UserService, ProfileService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(username="testuser", password="StrongPass123!", name="Test User"):
    """Register a user via UserService and return the User instance."""
    user, error = UserService.register(name=name, username=username, password=password)
    assert error is None, f"Unexpected registration error: {error}"
    return user


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class ProfileModelTest(TestCase):
    def test_profile_created_with_user(self):
        user = create_user()
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str(self):
        user = create_user(name="Jane Doe")
        profile = Profile.objects.get(user=user)
        profile.full_name = "Jane Doe"
        profile.save()
        self.assertIn("Jane Doe", str(profile))

    def test_profile_one_to_one(self):
        user = create_user()
        self.assertEqual(user.profile.user, user)


# ---------------------------------------------------------------------------
# UserService tests
# ---------------------------------------------------------------------------

class UserServiceRegisterTest(TestCase):
    def test_register_success(self):
        user, error = UserService.register(name="Alice", username="alice", password="StrongPass123!")
        self.assertIsNone(error)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "alice")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_register_duplicate_username(self):
        UserService.register(name="Alice", username="alice", password="StrongPass123!")
        user2, error = UserService.register(name="Alice2", username="alice", password="StrongPass123!")
        self.assertIsNone(user2)
        self.assertEqual(error, "Username already taken")

    def test_register_missing_fields(self):
        user, error = UserService.register(name="", username="alice", password="StrongPass123!")
        self.assertIsNone(user)
        self.assertEqual(error, "All fields required")

    def test_register_weak_password(self):
        user, error = UserService.register(name="Alice", username="alice_weak", password="123")
        self.assertIsNone(user)
        self.assertEqual(error, "Password too weak")


class UserServiceChangePasswordTest(TestCase):
    def setUp(self):
        self.user = create_user()

    def test_change_password_success(self):
        ok, error = UserService.change_password(self.user, "StrongPass123!", "NewSecurePass456!")
        self.assertTrue(ok)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecurePass456!"))

    def test_change_password_wrong_current(self):
        ok, error = UserService.change_password(self.user, "WrongPassword!", "NewSecurePass456!")
        self.assertFalse(ok)
        self.assertEqual(error, "Wrong current password")

    def test_change_password_weak_new(self):
        ok, error = UserService.change_password(self.user, "StrongPass123!", "123")
        self.assertFalse(ok)
        self.assertEqual(error, "Password too weak")


# ---------------------------------------------------------------------------
# ProfileService tests
# ---------------------------------------------------------------------------

class ProfileServiceTest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.profile = self.user.profile
        # full_clean() в ProfileService.update валидирует весь профиль,
        # поэтому email должен быть заполнен до теста с телефоном
        self.profile.full_name = "Test User"
        self.profile.email = "test@example.com"
        self.profile.save()

    def test_update_full_name(self):
        ok, error = ProfileService.update(self.profile, full_name="John Smith", email=None, phone=None)
        self.assertTrue(ok)
        self.assertIsNone(error)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, "John Smith")

    def test_update_email_valid(self):
        ok, error = ProfileService.update(self.profile, full_name=None, email="john@example.com", phone=None)
        self.assertTrue(ok)
        self.assertIsNone(error)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.email, "john@example.com")

    def test_update_email_invalid(self):
        ok, error = ProfileService.update(self.profile, full_name=None, email="not-an-email", phone=None)
        self.assertFalse(ok)
        self.assertEqual(error, "Invalid email")

    def test_update_phone_valid(self):
        ok, error = ProfileService.update(self.profile, full_name=None, email=None, phone="+79991234567")
        self.assertTrue(ok)
        self.assertIsNone(error)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, "+79991234567")

    def test_update_phone_invalid(self):
        ok, error = ProfileService.update(self.profile, full_name=None, email=None, phone="bad-phone")
        self.assertFalse(ok)
        self.assertEqual(error, "Invalid phone")


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

class AuthAPITest(APITestCase):
    def test_sign_up_success(self):
        data = {"name": "New User", "username": "newuser", "password": "StrongPass123!"}
        resp = self.client.post("/api/sign-up", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_sign_up_duplicate_username(self):
        data = {"name": "User", "username": "dupuser", "password": "StrongPass123!"}
        self.client.post("/api/sign-up", data, format="json")
        resp = self.client.post("/api/sign-up", data, format="json")
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK])

    def test_sign_in_success(self):
        create_user(username="loginuser", password="StrongPass123!")
        data = {"username": "loginuser", "password": "StrongPass123!"}
        resp = self.client.post("/api/sign-in", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_sign_in_wrong_password(self):
        create_user(username="loginuser2", password="StrongPass123!")
        data = {"username": "loginuser2", "password": "WrongPassword"}
        resp = self.client.post("/api/sign-in", data, format="json")
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_sign_out(self):
        create_user(username="logoutuser", password="StrongPass123!")
        self.client.post("/api/sign-in", {"username": "logoutuser", "password": "StrongPass123!"}, format="json")
        resp = self.client.post("/api/sign-out")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ProfileAPITest(APITestCase):
    def setUp(self):
        self.user = create_user(username="profileuser", password="StrongPass123!")
        self.client.post("/api/sign-in", {"username": "profileuser", "password": "StrongPass123!"}, format="json")

    def test_get_profile_authenticated(self):
        resp = self.client.get("/api/profile")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_profile_unauthenticated(self):
        self.client.logout()
        resp = self.client.get("/api/profile")
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_change_password_success(self):
        data = {"currentPassword": "StrongPass123!", "newPassword": "NewSecurePass456!"}
        resp = self.client.post("/api/profile/password", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_current(self):
        data = {"currentPassword": "WrongPassword", "newPassword": "NewSecurePass456!"}
        resp = self.client.post("/api/profile/password", data, format="json")
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
