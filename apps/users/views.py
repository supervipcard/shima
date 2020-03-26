import uuid
import base64
import random
from datetime import datetime
from captcha.image import ImageCaptcha
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django_redis import get_redis_connection
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import views, generics, mixins, viewsets, filters, status, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.views import ObtainJSONWebToken, jwt_response_payload_handler, api_settings

from .serializers import SMSCodeSerializer, UserRegSerializer, UserDetailSerializer, UserUpdateSerializer, ChangePasswordSerializer, ResetPasswordSerializer, CheckMobileSerializer, CustomJSONWebTokenSerializer

User = get_user_model()
redis_client = get_redis_connection("default")


class CustomBackend(ModelBackend):
    """
    自定义用户验证
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        try:
            user = User.objects.get(Q(username=username) | Q(phone=username))
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user


class UserViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """用户"""
    queryset = User.objects.all().order_by('id')
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)

    def get_permissions(self):
        if self.action in ["retrieve", "update", "partial_update", "change_password"]:
            return [permissions.IsAuthenticated()]
        elif self.action == "create":
            return []
        return []

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "create":
            return UserRegSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'reset_password':
            return ResetPasswordSerializer
        return UserDetailSerializer

    def get_object(self):
        return self.request.user

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        user.set_password(serializer.data['new_password'])
        user.save()
        return Response()

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(phone=serializer.data['phone'])
        user.set_password(serializer.data['password'])
        user.save()
        return Response()


class SMSCode(views.APIView):
    """
    短信验证码
    """
    number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def post(self, request):
        serializer = SMSCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.data['phone']
        code_list = random.choices(self.number, k=6)
        code_text = ''.join(code_list)
        message = '您的验证码是 {}，5分钟内有效，请勿泄露。'.format(code_text)
        print(message)
        key = 'smscode:{}'.format(phone)
        redis_client.set(key, code_text)
        redis_client.expire(key, 60*5)
        return Response(status=status.HTTP_201_CREATED)


class Captcha(views.APIView):
    number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def post(self, request):
        1/0
        code_list = random.choices(self.number + self.alphabet + self.ALPHABET, k=4)
        code_text = ''.join(code_list)
        image = ImageCaptcha()
        code = image.generate(code_text)
        code_base64 = base64.b64encode(code.read())
        code_uuid = str(uuid.uuid4())

        key = 'captcha:{}'.format(code_uuid)
        redis_client.set(key, code_text)
        redis_client.expire(key, 60)
        return Response({'uuid': code_uuid, 'code_base64': code_base64}, status=status.HTTP_201_CREATED)


class CheckMobile(views.APIView):
    def post(self, request):
        serializer = CheckMobileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response()


class CustomObtainJSONWebToken(ObtainJSONWebToken):
    serializer_class = CustomJSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.object.get('user') or request.user
        token = serializer.object.get('token')
        response_data = jwt_response_payload_handler(token, user, request)
        response = Response(response_data)
        if api_settings.JWT_AUTH_COOKIE:
            expiration = (datetime.utcnow() +
                          api_settings.JWT_EXPIRATION_DELTA)
            response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                token,
                                expires=expiration,
                                httponly=True)
        return response
