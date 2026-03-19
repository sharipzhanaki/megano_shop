import json

from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import UserSerializer
from .services import UserService, ProfileService
from orders.utils import sync_session_basket_to_db


class SignUpAPIView(APIView):
    """POST /sign-up - регистрация пользователя"""
    def post(self, request) -> Response:
        body = json.loads(request.body)
        user, error = UserService.register(
            name=body.get("name"),
            username=body.get("username"),
            password=body.get("password"),
        )
        if error:
            return Response(status=400)
        login(request, user)
        sync_session_basket_to_db(request)
        return Response(status=200)


class SignInAPIView(APIView):
    """POST /sign-in - авторизация"""
    def post(self, request) -> Response:
        body = json.loads(request.body)
        user = authenticate(request=request, username=body.get("username"), password=body.get("password"))
        if user is not None:
            login(request, user)
            sync_session_basket_to_db(request)
            return Response(status=200)
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
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def post(self, request) -> Response:
        if not request.user.is_authenticated:
            return Response(status=401)
        ok, error = ProfileService.update(
            profile=request.user.profile,
            full_name=request.data.get("fullName"),
            email=request.data.get("email"),
            phone=request.data.get("phone"),
        )
        if not ok:
            return Response({"error": error}, status=400)
        return Response(status=200)


class ChangePasswordAPIView(APIView):
    """POST /profile/password"""
    def post(self, request) -> Response:
        if not request.user.is_authenticated:
            return Response(status=401)
        ok, error = UserService.change_password(
            user=request.user,
            current=request.data.get("currentPassword"),
            new=request.data.get("newPassword"),
        )
        if not ok:
            return Response({"error": error}, status=400)
        return Response({"status": "ok"})


class UploadAvatarAPIView(APIView):
    """POST /profile/avatar"""
    def post(self, request) -> Response:
        if not request.user.is_authenticated:
            return Response(status=401)
        avatar = request.FILES.get("avatar")
        if not avatar:
            return Response(status=400)
        ProfileService.update_avatar(request.user.profile, avatar)
        return Response(status=200)
