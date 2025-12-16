from django.urls import path
from .views import (
    SignUpAPIView,
    SignInAPIView,
    SignOutAPIView,
    ProfileAPIView,
    ChangePasswordAPIView,
    UploadAvatarAPIView,
)


urlpatterns = [
    path("sign-up", SignUpAPIView.as_view(), name="sign-up"),
    path("sign-in", SignInAPIView.as_view(), name="sign-in"),
    path("sign-out", SignOutAPIView.as_view(), name="sign-out"),
    path("profile", ProfileAPIView.as_view(), name="profile"),
    path("profile/password", ChangePasswordAPIView.as_view(), name="profile_password"),
    path("profile/avatar", UploadAvatarAPIView.as_view(), name="profile_avatar"),
]
