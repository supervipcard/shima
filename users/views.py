import base64
import random
import json
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse

from captcha.image import ImageCaptcha
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.forms import Form, fields
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, resolve_url
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django_redis import get_redis_connection
from users.models import Wallet

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
            user = User.objects.get(Q(username=username) | Q(phone=username))
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user


class SendSMS(View):
    number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def post(self, request):
        phone = json.loads(request.body).get('phone')
        if phone:
            text_list = random.choices(self.number + self.alphabet + self.ALPHABET, k=4)
            code_text = ''.join(text_list)
            message = '你的验证码是 {}'.format(code_text)
            print(message)
            key = 'smscode:{}'.format(phone)
            rs.set(key, code_text)
            rs.expire(key, 60)
            return JsonResponse({'code': 0, 'message': '短信发送成功'})
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
    phone = fields.RegexField(r'^\d{11}$')
    sms_code = fields.CharField()
    password = fields.CharField()


class Register(View):
    def post(self, request):
        form = RegisterForm(json.loads(request.body))
        if form.is_valid():
            username = form.cleaned_data['username']
            phone = form.cleaned_data['phone']
            sms_code = form.cleaned_data['sms_code']
            password = form.cleaned_data['password']

            key = 'smscode:{}'.format(phone)
            val = rs.get(key)
            if not val or val.decode('utf8').lower() != sms_code.lower():
                return JsonResponse({'code': 2001, 'message': '验证码错误'})
            try:
                User.objects.get(phone=phone)
            except User.DoesNotExist:
                pass
            else:
                return JsonResponse({'code': 2002, 'message': '手机号已注册'})
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                pass
            else:
                return JsonResponse({'code': 2003, 'message': '用户名已存在'})
            user = User(username=username, phone=phone, password=password)
            user.set_password(password)
            user.save()
            Wallet.objects.create(user=user)
            return JsonResponse({"code": 0, "message": "注册成功"})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class SignInView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('index')
        next_page = request.GET.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = resolve_url('index')
        code_id = str(uuid.uuid1())
        return render(request, 'sign_in.html', {"code_id": code_id, 'next_page': next_page})


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


class VerifyPhoneForm(Form):
    phone = fields.CharField()
    code_text = fields.CharField()
    code_id = fields.CharField()


class VerifyPhone(View):
    def post(self, request):
        form = VerifyPhoneForm(json.loads(request.body))
        if form.is_valid():
            phone = form.cleaned_data['phone']
            code_text = form.cleaned_data['code_text']
            code_id = form.cleaned_data['code_id']

            key = 'captcha:{}'.format(code_id)
            val = rs.get(key)
            if not val or val.decode('utf8').lower() != code_text.lower():
                return JsonResponse({'code': 4001, 'message': '验证码错误'})
            try:
                User.objects.get(phone=phone)
                response = JsonResponse({"code": 0, "message": "手机号验证成功"})
                response.set_cookie('phone', phone)
                return response
            except User.DoesNotExist:
                return JsonResponse({'code': 4002, 'message': '手机号不存在'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class ForgetPasswordView2(View):
    def get(self, request):
        phone = request.COOKIES.get('phone')
        if phone:
            return render(request, 'forget_password2.html', {'phone': phone})
        else:
            return redirect('forget_password')


class ResetPasswordForm(Form):
    phone = fields.CharField()
    sms_code = fields.CharField()
    password = fields.CharField()


class ResetPassword(View):
    def post(self, request):
        form = ResetPasswordForm(json.loads(request.body))
        if form.is_valid():
            phone = form.cleaned_data['phone']
            sms_code = form.cleaned_data['sms_code']
            password = form.cleaned_data['password']

            key = 'smscode:{}'.format(phone)
            val = rs.get(key)
            if not val or val.decode('utf8').lower() != sms_code.lower():
                return JsonResponse({'code': 5001, 'message': '验证码错误'})
            try:
                user = User.objects.get(phone=phone)
                user.set_password(password)
                user.save()
                return JsonResponse({"code": 0, "message": "密码重置成功"})
            except User.DoesNotExist:
                return JsonResponse({'code': 5002, 'message': '手机号不存在'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class ChangePasswordForm(Form):
    old_password = fields.CharField()
    new_password = fields.CharField()


class ChangePassword(View):
    @method_decorator(login_required)
    def post(self, request):
        form = ChangePasswordForm(json.loads(request.body))
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            user = request.user
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                login(request, user)
                return JsonResponse({"code": 0, "message": "密码修改成功"})
            else:
                return JsonResponse({"code": 6001, "message": "当前密码错误"})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class Logout(View):
    def post(self, request):
        logout(request)
        return JsonResponse({"code": 0, "message": "登出成功"})

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(Logout, self).dispatch(*args, **kwargs)
