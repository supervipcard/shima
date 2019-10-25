import json
import time
import random
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
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
from .serializers import *
from .filters import *
from .alipay_utils import AliPayModule
from.redis_expired import TimeoutController

controller = TimeoutController()


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


class OrderDetails(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        order = Order.objects.get(order_id=pk)
        if order.transaction_type == 1:
            order_product = None
        else:
            order_product = OrderProduct.objects.get(order=order)
        order_url = AliPayModule.pay(order.order_id, order.amount) if order.pay_status == 1 else None
        return render(request, 'order_details.html', {'order': order, 'order_product': order_product, 'order_url': order_url})


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
            controller.countdown(order_id)
            return JsonResponse({"code": 0, "message": '下单成功', 'data': {'order_id': order_id}})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class OrderCancel(View):
    @method_decorator(login_required)
    def post(self, request):
        form = json.loads(request.body)
        if form.get('order_id_list'):
            order_id_list = form['order_id_list']
            for order_id in order_id_list:
                order = Order.objects.get(order_id=order_id)
                order.pay_status = 4
                order.save()
                AliPayModule.close(order_id)
            return JsonResponse({"code": 0, "message": '订单删除成功'})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(OrderCancel, self).dispatch(*args, **kwargs)


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
            controller.countdown(order_id)
            return JsonResponse({"code": 0, "message": '下单成功', 'data': {'order_id': order_id}})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class RenewForm(Form):
    channel_id = fields.CharField()
    product_package_id = fields.CharField()
    period = fields.CharField()


class Renew(View):
    @method_decorator(login_required)
    def post(self, request):
        form = RenewForm(json.loads(request.body))
        if form.is_valid():
            product_package_id = form.cleaned_data['product_package_id']
            period = form.cleaned_data['period']
            channel_id = form.cleaned_data['channel_id']

            product_package = ProductPackage.objects.get(id=product_package_id)
            channel = InterfaceChannel.objects.get(id=channel_id)
            additional_concurrency = channel.concurrency-product_package.default_concurrency

            user = request.user
            order_id = "{time_str}{userid}{ranstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"), userid=request.user.id, ranstr=random.randint(10000, 99999))
            amount = product_package.price * int(period) + product_package.additional_concurrency_price * additional_concurrency
            order = Order(user=user, order_id=order_id, transaction_type=3, amount=amount)
            order.save()
            order_product = OrderProduct(order=order, product_package=product_package, channel=channel, period=period)
            order_product.save()
            controller.countdown(order_id)
            return JsonResponse({"code": 0, "message": '下单成功', 'data': {'order_id': order_id}})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class UpgradeForm(Form):
    channel_id = fields.CharField()
    new_additional_concurrency = fields.CharField()
    price = fields.CharField()


class Upgrade(View):
    @method_decorator(login_required)
    def post(self, request):
        form = UpgradeForm(json.loads(request.body))
        if form.is_valid():
            new_additional_concurrency = form.cleaned_data['new_additional_concurrency']
            channel_id = form.cleaned_data['channel_id']
            price = form.cleaned_data['price']

            channel = InterfaceChannel.objects.get(id=channel_id)

            user = request.user
            order_id = "{time_str}{userid}{ranstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"), userid=request.user.id, ranstr=random.randint(10000, 99999))
            amount = float(price) * int(new_additional_concurrency)
            order = Order(user=user, order_id=order_id, transaction_type=4, amount=amount)
            order.save()
            order_product = OrderProduct(order=order, channel=channel, new_additional_concurrency=new_additional_concurrency)
            order_product.save()
            controller.countdown(order_id)
            return JsonResponse({"code": 0, "message": '下单成功', 'data': {'order_id': order_id}})
        else:
            return JsonResponse({'code': 1001, 'message': '请求参数异常'})


class AliPayAPIView(View):
    def get(self, request):
        data = request.GET.dict()
        sign = data.pop('sign')
        result = AliPayModule.verify(data, sign)
        if result:
            return HttpResponseRedirect(reverse('account_order'))
        else:
            return HttpResponseForbidden()

    def post(self, request):
        data = request.POST.dict()
        sign = data.pop('sign')
        result = AliPayModule.verify(data, sign)
        if result:
            order_id = data['out_trade_no']
            order = Order.objects.get(order_id=order_id)
            order.trade_no = data['trade_no']
            order.pay_time = datetime.now()
            order.pay_status = 2
            order.save()
            controller.delete(order_id)

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
                    channel = InterfaceChannel(user=user, product=product_package.product, concurrency=concurrency, creation_time=creation_time, expiration_time=expiration_time)
                    channel.save()
            elif transaction_type == 3:
                order_product = OrderProduct.objects.get(order=order)
                product_package = order_product.product_package
                channel = order_product.channel
                total_hours = {1: 1 / 24, 2: 1, 3: 7, 4: 30, 5: 90, 6: 365}.get(product_package.time_limit) * 24 * order_product.period
                channel.renewal_time = datetime.now()
                channel.expiration_time = channel.expiration_time + timedelta(hours=total_hours)
                channel.save()
            elif transaction_type == 4:
                order_product = OrderProduct.objects.get(order=order)
                channel = order_product.channel
                channel.concurrency = channel.concurrency + order_product.new_additional_concurrency
                channel.save()

            return HttpResponse('success')
        else:
            return HttpResponse('failure')

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(AliPayAPIView, self).dispatch(*args, **kwargs)
