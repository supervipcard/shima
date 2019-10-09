from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.forms import Form, fields
import json
import time
import random

from .models import *
from users.models import *


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


class HomePage(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        wallet = Wallet.objects.get(user=user)
        return render(request, 'home/homepage2.html', {'user': user, 'wallet': wallet})


class Operate(View):
    @method_decorator(login_required)
    def get(self, request):
        return render(request, 'operate.html')


class OrderPlaceForm(Form):
    product_package_id = fields.CharField()
    period = fields.CharField()
    number = fields.CharField()
    additional_concurrency = fields.CharField()


class OrderPlace(View):
    @method_decorator(login_required)
    def post(self, request):
        form = OrderPlaceForm(json.loads(request.body))
        if form.is_valid():
            product_package_id = form.cleaned_data['product_package_id']
            period = form.cleaned_data['period']
            number = form.cleaned_data['number']
            additional_concurrency = form.cleaned_data['additional_concurrency']

            product_package = ProductPackage.objects.get(id=product_package_id)

            user = request.user
            order_id = time.time() + random.randint(10000, 99999)
            transaction_type = 2
            amount = product_package.price * period * number
            order = Order(user=user, order_id=order_id, transaction_type=transaction_type, amount=amount)
            order.save()
            order_product = OrderProduct(order=order, product_package=product_package, period=period, number=number, additional_concurrency=additional_concurrency)
            order_product.save()
            return JsonResponse({"code": 0, "message": '下单成功'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})
