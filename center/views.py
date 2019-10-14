from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.forms import Form, fields
from datetime import datetime, timedelta
import json
import time
import random

from .models import *
from users.models import *
from center.alipay_utils import AliPayModule


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
            order_id = "{time_str}{userid}{ranstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"), userid=request.user.id, ranstr=random.randint(10000, 99999))
            amount = product_package.price * int(period) * int(number) + product_package.additional_concurrency_price * int(additional_concurrency)
            order = Order(user=user, order_id=order_id, transaction_type=2, amount=amount)
            order.save()
            order_product = OrderProduct(order=order, product_package=product_package, period=period, number=number, additional_concurrency=additional_concurrency)
            order_product.save()
            order_url = AliPayModule.pay(order_id, amount)
            return JsonResponse({"code": 0, "message": '下单成功', 'data': {'order_url': order_url}})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class AliPayView(View):
    def get(self, request):
        data = request.GET.dict()
        sign = data.pop('sign')
        result = AliPayModule.verify(data, sign)
        print(result)
        if result:
            return HttpResponse('success')
        else:
            return HttpResponse('failure')

    def post(self, request):
        data = request.POST.dict()
        sign = data.pop('sign')
        result = AliPayModule.verify(data, sign)
        print(result)
        if result:
            order_id = data['out_trade_no']
            order = Order.objects.get(order_id=order_id)
            order.trade_no = data['trade_no']
            order.pay_time = datetime.now()
            order.pay_status = 2
            order.save()

            order_product = OrderProduct.objects.get(order=order)
            user = order_product.order.user
            product_package = order_product.product_package
            concurrency = order_product.product_package.default_concurrency + order_product.additional_concurrency
            creation_time = datetime.now()
            if order_product.product_package.time_limit == 1:
                expiration_time = creation_time + timedelta(hours=order_product.product_package.time_limit * order_product.period)
            else:
                expiration_time = creation_time + timedelta(days={2: 1, 3: 7, 4: 30, 5: 90, 6: 365}.get(order_product.product_package.time_limit) * order_product.period)
            for i in range(order_product.number):
                channel = InterfaceChannel(user=user, product_package=product_package, concurrency=concurrency, creation_time=creation_time, expiration_time=expiration_time)
                channel.save()
            return HttpResponse('success')
        else:
            return HttpResponse('failure')

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(AliPayView, self).dispatch(*args, **kwargs)
