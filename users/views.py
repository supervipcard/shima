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

from users.models import EmailCode, Captcha

User = get_user_model()


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


class SignUpForm(Form):
    username = fields.CharField()
    email = fields.EmailField()
    email_code = fields.CharField()
    password = fields.CharField()


class SignUpView(View):
    def get(self, request):
        return render(request, 'sign_up.html')


class Register(View):
    def post(self, request):
        form = SignUpForm(json.loads(request.body))
        ret = {"code": 0, "message": "注册成功"}
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            email_code = form.cleaned_data['email_code']
            password = form.cleaned_data['password']

            try:
                User.objects.get(email=email)
            except User.DoesNotExist:
                pass
            else:
                ret['code'] = 2001
                ret['message'] = '邮箱已注册'
                return JsonResponse(ret)
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                pass
            else:
                ret['code'] = 2002
                ret['message'] = '用户名已存在'
                return JsonResponse(ret)

            code_set = EmailCode.objects.filter(email=email).order_by("-add_time")
            if code_set:
                last_code = code_set[0]
                five_minutes_ago = datetime.now() - timedelta(hours=0, minutes=1, seconds=0)
                if five_minutes_ago > last_code.add_time:
                    ret['code'] = 2003
                    ret['message'] = '验证码已过期，请重新发送'
                    return JsonResponse(ret)
                elif last_code.code_text.lower() != email_code.lower():
                    ret['code'] = 2004
                    ret['message'] = '验证码错误'
                    return JsonResponse(ret)
                else:
                    user = User(username=username, email=email, password=password)
                    user.set_password(password)
                    user.save()
                    return JsonResponse(ret)
            else:
                ret['code'] = 2004
                ret['message'] = '验证码错误'
                return JsonResponse(ret)
        else:
            ret['code'] = 1001
            ret['message'] = '请求参数异常'
            return JsonResponse(ret)


class EmailCodeView(View):
    number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def send_code(self, email):
        text_list = random.choices(self.number + self.alphabet + self.ALPHABET, k=4)
        code_text = ''.join(text_list)
        message = '你的验证码是 {}'.format(code_text)
        print(message)
        # send_mail('测试', message, '805071841@qq.com', [email], fail_silently=True)
        return code_text

    def post(self, request):
        email = json.loads(request.body).get('email')
        if email:
            code_text = self.send_code(email)
            EmailCode.objects.create(email=email, code_text=code_text)
            return JsonResponse({'code': 0, 'message': '邮件发送成功'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class SignInForm(Form):
    username = fields.CharField()
    password = fields.CharField()
    code_text = fields.CharField()
    code_id = fields.CharField()


class SignInView(View):
    def get(self, request):
        code_id = str(uuid.uuid1())
        return render(request, 'sign_in.html', {"code_id": code_id})


class Login(View):
    def post(self, request):
        form = SignInForm(json.loads(request.body))
        ret = {"code": 0, "message": "登录成功"}
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            code_text = form.cleaned_data['code_text']
            code_id = form.cleaned_data['code_id']

            code_set = Captcha.objects.filter(code_id=code_id).order_by("-add_time")
            if code_set:
                last_code = code_set[0]
                if last_code.code_text.lower() != code_text.lower():
                    ret['code'] = 3001
                    ret['message'] = '验证码错误'
                    return JsonResponse(ret)
                else:
                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)
                        return JsonResponse(ret)
                    else:
                        ret['code'] = 3002
                        ret['message'] = '用户名或密码错误'
                        return JsonResponse(ret)
            else:
                ret['code'] = 3001
                ret['message'] = '验证码错误'
                return JsonResponse(ret)
        else:
            ret['code'] = 1001
            ret['message'] = '请求参数异常'
            return JsonResponse(ret)


class CaptchaView(View):
    number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z']
    ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z']

    def generate_code(self):
        text_list = random.choices(self.number + self.alphabet + self.ALPHABET, k=4)
        code_text = ''.join(text_list)
        image = ImageCaptcha()
        code = image.generate(code_text)
        code_bytes = code.read()
        return code_text, code_bytes

    def get(self, request):
        code_text, code_bytes = self.generate_code()
        code_id = request.GET.get('u')
        if code_id:
            Captcha.objects.create(code_id=code_id, code_text=code_text)
        return HttpResponse(code_bytes, content_type="image/png")


class CheckEmailForm(Form):
    email = fields.EmailField()
    code_text = fields.CharField()
    code_id = fields.CharField()


class ForgetPasswordView(View):
    def get(self, request):
        code_id = str(uuid.uuid1())
        return render(request, 'forget_password.html', {'code_id': code_id})


class CheckEmail(View):
    def post(self, request):
        form = CheckEmailForm(json.loads(request.body))
        ret = {"code": 0, "message": "成功"}
        if form.is_valid():
            email = form.cleaned_data['email']
            code_text = form.cleaned_data['code_text']
            code_id = form.cleaned_data['code_id']

            code_set = Captcha.objects.filter(code_id=code_id).order_by("-add_time")
            if code_set:
                last_code = code_set[0]
                if last_code.code_text.lower() != code_text.lower():
                    ret['code'] = 4001
                    ret['message'] = '验证码错误'
                    return JsonResponse(ret)
                else:
                    try:
                        User.objects.get(email=email)
                        response = JsonResponse(ret)
                        response.set_cookie('email', email)
                        return response
                    except User.DoesNotExist:
                        ret['code'] = 4002
                        ret['message'] = '邮箱未注册'
                        return JsonResponse(ret)
            else:
                ret['code'] = 4001
                ret['message'] = '验证码错误'
                return JsonResponse(ret)
        else:
            ret['code'] = 1001
            ret['message'] = '请求参数异常'
            return JsonResponse(ret)


class ResetPasswordForm(Form):
    email = fields.EmailField()
    email_code = fields.CharField()
    password = fields.CharField()


class ResetPasswordView(View):
    def get(self, request):
        email = request.COOKIES.get('email')
        if email:
            return render(request, 'reset_password.html', {'email': email})
        else:
            return redirect('forget-password')


class ResetPassword(View):
    def post(self, request):
        form = ResetPasswordForm(json.loads(request.body))
        ret = {"code": 0, "message": "密码修改成功"}
        if form.is_valid():
            email = form.cleaned_data['email']
            email_code = form.cleaned_data['email_code']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                ret['code'] = 5001
                ret['message'] = '邮箱未注册'
                return JsonResponse(ret)

            code_set = EmailCode.objects.filter(email=email).order_by("-add_time")
            if code_set:
                last_code = code_set[0]
                five_minutes_ago = datetime.now() - timedelta(hours=0, minutes=1, seconds=0)
                if five_minutes_ago > last_code.add_time:
                    ret['code'] = 5003
                    ret['message'] = '验证码已过期，请重新发送'
                    return JsonResponse(ret)
                elif last_code.code_text.lower() != email_code.lower():
                    ret['code'] = 5004
                    ret['message'] = '验证码错误'
                    return JsonResponse(ret)
                else:
                    user.set_password(password)
                    user.save()
                    return JsonResponse(ret)
            else:
                ret['code'] = 5004
                ret['message'] = '验证码错误'
                return JsonResponse(ret)
        else:
            ret['code'] = 1001
            ret['message'] = '请求参数异常'
            return JsonResponse(ret)
