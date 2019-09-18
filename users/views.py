import base64
import random
import json
import uuid
from datetime import datetime, timedelta

from captcha.image import ImageCaptcha
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.backends import ModelBackend
from django.core.mail import send_mail
from django.db.models import Q
from django.forms import Form, fields
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django_redis import get_redis_connection

User = get_user_model()

rs = get_redis_connection("default")


class CustomBackend(ModelBackend):
    """
    自定义用户验证
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user


class SendEmail(View):
    number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def post(self, request):
        email = json.loads(request.body).get('email')
        if email:
            text_list = random.choices(self.number + self.alphabet + self.ALPHABET, k=4)
            code_text = ''.join(text_list)
            message = '你的验证码是 {}'.format(code_text)
            print(message)
            key = 'emailcode:{}'.format(email)
            rs.set(key, code_text)
            rs.expire(key, 60)
            return JsonResponse({'code': 0, 'message': '邮件发送成功'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class CreateCaptcha(View):
    number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def get(self, request):
        text_list = random.choices(self.number + self.alphabet + self.ALPHABET, k=4)
        code_text = ''.join(text_list)
        image = ImageCaptcha()
        code = image.generate(code_text)
        code_bytes = code.read()

        code_id = request.GET.get('u')
        if code_id:
            key = 'captcha:{}'.format(code_id)
            rs.set(key, code_text)
            rs.expire(key, 60)
        return HttpResponse(code_bytes, content_type="image/png")


class SignUpView(View):
    def get(self, request):
        return render(request, 'sign_up.html')


class RegisterForm(Form):
    username = fields.CharField()
    email = fields.EmailField()
    email_code = fields.CharField()
    password = fields.CharField()


class Register(View):
    def post(self, request):
        form = RegisterForm(json.loads(request.body))
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            email_code = form.cleaned_data['email_code']
            password = form.cleaned_data['password']

            key = 'emailcode:{}'.format(email)
            val = rs.get(key)
            if not val or val.decode('utf8').lower() != email_code.lower():
                return JsonResponse({'code': 2001, 'message': '邮箱验证码错误'})
            try:
                User.objects.get(email=email)
            except User.DoesNotExist:
                pass
            else:
                return JsonResponse({'code': 2002, 'message': '邮箱已注册'})
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                pass
            else:
                return JsonResponse({'code': 2003, 'message': '用户名已存在'})
            user = User(username=username, email=email, password=password)
            user.set_password(password)
            user.save()
            return JsonResponse({"code": 0, "message": "注册成功"})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class SignInView(View):
    def get(self, request):
        code_id = str(uuid.uuid1())
        return render(request, 'sign_in.html', {"code_id": code_id})


class LoginForm(Form):
    username = fields.CharField()
    password = fields.CharField()
    code_text = fields.CharField()
    code_id = fields.CharField()


class Login(View):
    def post(self, request):
        form = LoginForm(json.loads(request.body))
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            code_text = form.cleaned_data['code_text']
            code_id = form.cleaned_data['code_id']

            key = 'captcha:{}'.format(code_id)
            val = rs.get(key)
            if not val or val.decode('utf8').lower() != code_text.lower():
                return JsonResponse({'code': 3001, 'message': '验证码错误'})
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return JsonResponse({"code": 0, "message": "登录成功"})
            else:
                return JsonResponse({'code': 3002, 'message': '用户名或密码错误'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class ForgetPasswordView(View):
    def get(self, request):
        code_id = str(uuid.uuid1())
        return render(request, 'forget_password.html', {'code_id': code_id})


class VerifyEmailForm(Form):
    email = fields.EmailField()
    code_text = fields.CharField()
    code_id = fields.CharField()


class VerifyEmail(View):
    def post(self, request):
        form = VerifyEmailForm(json.loads(request.body))
        if form.is_valid():
            email = form.cleaned_data['email']
            code_text = form.cleaned_data['code_text']
            code_id = form.cleaned_data['code_id']

            key = 'captcha:{}'.format(code_id)
            val = rs.get(key)
            if not val or val.decode('utf8').lower() != code_text.lower():
                return JsonResponse({'code': 4001, 'message': '验证码错误'})
            try:
                User.objects.get(email=email)
                response = JsonResponse({"code": 0, "message": "邮箱验证成功"})
                response.set_cookie('email', email)
                return response
            except User.DoesNotExist:
                return JsonResponse({'code': 4002, 'message': '邮箱未注册'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class ForgetPasswordView2(View):
    def get(self, request):
        email = request.COOKIES.get('email')
        if email:
            return render(request, 'forget_password2.html', {'email': email})
        else:
            return redirect('forget_password')


class ResetPasswordForm(Form):
    email = fields.EmailField()
    email_code = fields.CharField()
    password = fields.CharField()


class ResetPassword(View):
    def post(self, request):
        form = ResetPasswordForm(json.loads(request.body))
        if form.is_valid():
            email = form.cleaned_data['email']
            email_code = form.cleaned_data['email_code']
            password = form.cleaned_data['password']

            key = 'emailcode:{}'.format(email)
            val = rs.get(key)
            if not val or val.decode('utf8').lower() != email_code.lower():
                return JsonResponse({'code': 5001, 'message': '邮箱验证码错误'})
            try:
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                return JsonResponse({"code": 0, "message": "密码重置成功"})
            except User.DoesNotExist:
                return JsonResponse({'code': 5002, 'message': '邮箱未注册'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})
