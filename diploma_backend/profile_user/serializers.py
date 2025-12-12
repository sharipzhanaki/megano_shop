from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Profile


class AvatarSerializer(serializers.Serializer):
    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    def get_src(self, profile: Profile):
        if profile.avatar:
            return self.context["request"].build_absolute_uri(profile.avatar.url)
        return None

    def get_alt(self, profile: Profile):
        return profile.full_name if profile.full_name else ""


class UserSerializer(serializers.Serializer):
    fullName = serializers.CharField(source="profile.full_name")
    email = serializers.EmailField(source="profile.email")
    phone = serializers.CharField(source="profile.phone")
    avatar = AvatarSerializer(source="profile", required=False)

    class Meta:
        model = User
        fields = ("fullName", "email", "phone", "avatar")
