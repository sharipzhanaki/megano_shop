import json

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Profile
from .serializers import UserSerializer
from orders.utils import sync_session_basket_to_db


class SignUpAPIView(APIView):
    """POST /sign-up - регистрация пользователя"""
    def post(self, request) -> Response:
        body = json.loads(request.body)
        name = body["name"]
        username = body["username"]
        password = body["password"]
        if not all([name, username, password]):
            return Response(status=400)
        if User.objects.filter(username=username).exists():
            return Response(status=400)
        try:
            validate_password(password)
        except ValidationError:
            return Response(status=400)
        user = User.objects.create_user(first_name=name, username=username, password=password)
        user.save()
        Profile.objects.create(user=user)
        login(request, user)
        sync_session_basket_to_db(request)
        return Response(status=200)


class SignInAPIView(APIView):
    """POST /sign-in - авторизация"""
    def post(self, request) -> Response:
        body = json.loads(request.body)
        username = body["username"]
        password = body["password"]
        user = authenticate(request=request, username=username, password=password)
        if user is not None:
            login(request, user)
            sync_session_basket_to_db(request)
            return Response(status=200)
        else:
            return Response(status=500)


class SignOutAPIView(APIView):
    """POST /sign-out - выход"""
    def post(self, request) -> Response:
        logout(request)
        return Response({"status": "ok"})


class ProfileAPIView(APIView):
    """GET or POST /profile - получить или изменить профиль"""
    def get(self, request) -> Response:
        if not request.user.is_authenticated:
            return Response(status=401)
        return Response(UserSerializer(request.user, context={"request": request}).data, status=200)

    def post(self, request) -> Response:
        if not request.user.is_authenticated:
            return Response(status=401)
        data = request.data
        profile = request.user.profile
        full_name = data.get("fullName")
        email = data.get("email")
        phone = data.get("phone")
        if full_name is not None:
            profile.full_name = full_name
        if email is not None:
            try:
                validate_email(email)
            except ValidationError:
                return Response(status=400)
            profile.email = email
        if phone is not None:
            profile.phone = phone
            try:
                profile.full_clean()
            except ValidationError:
                return Response(status=400)
        profile.save()
        return Response(status=200)


class ChangePasswordAPIView(APIView):
    """POST /profile/password"""
    def post(self, request) -> Response:
        if not request.user.is_authenticated:
            return Response(status=401)
        data = request.data
        current = data.get("currentPassword")
        new = data.get("newPassword")
        user = request.user
        if not user.check_password(current):
            return Response(status=400)
        try:
            validate_password(new)
        except ValidationError:
            return Response(400)
        user.set_password(new)
        user.save()
        return Response({"status": "ok"})


class UploadAvatarAPIView(APIView):
    """POST /profile/avatar"""
    def post(self, request) -> Response:
        if not request.user.is_authenticated:
            return Response(status=401)
        avatar = request.FILES.get("avatar")
        if not avatar:
            return Response(status=400)
        profile = request.user.profile
        profile.avatar = avatar
        profile.save()
        return Response(status=200)
