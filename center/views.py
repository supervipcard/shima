import json
import time
import random
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.forms import Form, fields
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import *
from users.models import *
from .alipay_utils import AliPayModule
from .serializers import *
from .filters import *


def global_setting(request):
    products = Product.objects.all()
    return {'products': products}


class Index(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        wallet = Wallet.objects.get(user=user)
        channel_num = len(InterfaceChannel.objects.filter(user=user))
        return render(request, 'index.html', {'user': user, 'wallet': wallet, 'channel_num': channel_num})


class AccountProfile(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        return render(request, 'account_profile.html', {'user': user})


class AccountWallet(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        wallet = Wallet.objects.get(user=user)
        return render(request, 'account_wallet.html', {'user': user, 'wallet': wallet})


class AccountOrder(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)
        return render(request, 'account_order.html', {'user': user, 'orders': orders})


class Service(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        user = request.user
        product = Product.objects.get(id=pk)
        product_package = ProductPackage.objects.filter(product=product)
        # channel = InterfaceChannel.objects.filter(Q(user=user), Q(product_package__product=product))
        return render(request, 'service.html', {'user': user, 'product': product, 'product_package': product_package})


class OrderListAPIView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (SessionAuthentication, )
    serializer_class = OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-add_time')


class ChannelListAPIView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (SessionAuthentication, )
    serializer_class = ChannelSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = ChannelFilter

    def get_queryset(self):
        return InterfaceChannel.objects.filter(user=self.request.user).order_by('-creation_time')


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


class WalletTopUpForm(Form):
    amount = fields.CharField()


class WalletTopUp(View):
    @method_decorator(login_required)
    def post(self, request):
        form = WalletTopUpForm(json.loads(request.body))
        if form.is_valid():
            amount = form.cleaned_data['amount']
            user = request.user
            order_id = "{time_str}{userid}{ranstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"), userid=request.user.id, ranstr=random.randint(10000, 99999))
            order = Order(user=user, order_id=order_id, transaction_type=1, amount=amount)
            order.save()
            order_url = AliPayModule.pay(order_id, amount)
            return JsonResponse({"code": 0, "message": '下单成功', 'data': {'order_url': order_url}})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class AliPayAPIView(View):
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

            user = order.user
            transaction_type = order.transaction_type
            if transaction_type == 1:
                wallet = Wallet.objects.get(user=user)
                wallet.balance += order.amount
                wallet.save()
            elif transaction_type == 2:
                order_product = OrderProduct.objects.get(order=order)
                product_package = order_product.product_package
                concurrency = product_package.default_concurrency + order_product.additional_concurrency
                creation_time = datetime.now()
                total_hours = {1: 1/24, 2: 1, 3: 7, 4: 30, 5: 90, 6: 365}.get(product_package.time_limit) * 24 * order_product.period
                expiration_time = creation_time + timedelta(hours=total_hours)
                for i in range(order_product.number):
                    channel = InterfaceChannel(user=user, product_package=product_package, concurrency=concurrency, creation_time=creation_time, expiration_time=expiration_time)
                    channel.save()
            return HttpResponse('success')
        else:
            return HttpResponse('failure')

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(AliPayAPIView, self).dispatch(*args, **kwargs)
