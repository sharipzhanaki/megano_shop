from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import Profile


class UserService:
    @staticmethod
    def register(name: str, username: str, password: str):
        """Зарегистрировать пользователя и создать профиль.
        Возвращает (user, ошибка)."""
        if not all([name, username, password]):
            return None, "All fields required"
        if User.objects.filter(username=username).exists():
            return None, "Username already taken"
        try:
            validate_password(password)
        except ValidationError:
            return None, "Password too weak"
        user = User.objects.create_user(first_name=name, username=username, password=password)
        Profile.objects.create(user=user)
        return user, None

    @staticmethod
    def change_password(user: User, current: str, new: str):
        """Сменить пароль. Возвращает (успех, ошибка)."""
        if not user.check_password(current):
            return False, "Wrong current password"
        try:
            validate_password(new)
        except ValidationError:
            return False, "Password too weak"
        user.set_password(new)
        user.save()
        return True, None


class ProfileService:
    @staticmethod
    def update(profile: Profile, full_name: str | None, email: str | None, phone: str | None):
        """Обновить поля профиля. Возвращает (успех, ошибка)."""
        if full_name is not None:
            profile.full_name = full_name
        if email is not None:
            try:
                validate_email(email)
            except ValidationError:
                return False, "Invalid email"
            profile.email = email
        if phone is not None:
            profile.phone = phone
            try:
                profile.full_clean()
            except ValidationError:
                return False, "Invalid phone"
        profile.save()
        return True, None

    @staticmethod
    def update_avatar(profile: Profile, avatar) -> None:
        profile.avatar = avatar
        profile.save()
