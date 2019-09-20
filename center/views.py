from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .models import *


def global_setting(request):
    product = Product.objects.all()
    return {'product': product}


class Index(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        return render(request, 'index.html', {'user': user})


class UserInfo(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        return render(request, 'set/user/info.html', {'user': user})


class UserPassword(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        return render(request, 'set/user/password.html', {'user': user})
