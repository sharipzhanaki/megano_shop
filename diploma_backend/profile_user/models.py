from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


def avatar_upload_path(instance: "Profile", filename:str) -> str:
    return  f"profiles/user_{instance.pk}/avatars/{filename}"


class Profile(models.Model):
    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=200)
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+[1-9]\d{9,15}$',
                message="Phone number must be with optional +"
            )
        ],
        blank=True
    )
    avatar = models.ImageField(blank=True, null=True, upload_to=avatar_upload_path)

    def __str__(self):
        return f"Profile of {self.full_name}"
