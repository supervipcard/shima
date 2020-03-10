from datetime import datetime, timedelta
from django.http import HttpResponseForbidden
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import views, mixins, viewsets, status, permissions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from .serializers import *
from utils.alipay_ import Alipay
from utils.redis_expired import TimeoutController
from utils.permissions import IsSelf

controller = TimeoutController()


class ProductViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Product.objects.all().order_by('id')
    serializer_class = ProductSerializer
    pagination_class = None


class ProductPackageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = ProductPackage.objects.all().order_by('id')
    serializer_class = ProductPackageSerializer
    pagination_class = None


class OrderViewSet(mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsSelf)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-add_time')

    def get_serializer_class(self):
        if self.action == "purchase":
            return OrderPurchaseSerializer
        return OrderSerializer

    @action(detail=False, methods=['post'])
    def purchase(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)


class OrderGoodsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsSelf)
    serializer_class = OrderGoodsSerializer

    def get_queryset(self):
        return OrderGoods.objects.filter(user=self.request.user).order_by('id')


class ServiceViewSet(mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    authentication_classes = (JSONWebTokenAuthentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsSelf)
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return Service.objects.filter(user=self.request.user).order_by('id')


class AliPayAPIView(views.APIView):
    def get(self, request):
        data = request.GET.dict()
        sign = data.pop('sign')
        result = Alipay.verify(data, sign)
        if result:
            return Response('Hello World!')
        else:
            return HttpResponseForbidden()

    def post(self, request):
        data = request.POST.dict()
        sign = data.pop('sign')
        result = Alipay.verify(data, sign)
        if result:
            order_id = data['out_trade_no']
            try:
                order = Order.objects.get(order_id=order_id)
                order_goods = OrderGoods.objects.get(order=order)
            except Order.DoesNotExist or OrderGoods.DoesNotExist:
                return Response('failure')
            order.trade_no = data['trade_no']
            order.pay_channel = 2
            order.pay_status = 2
            order.pay_time = datetime.now()
            order.save()

            user = order.user
            transaction_type = order.transaction_type
            if transaction_type == 2:
                concurrency = order_goods.product_package.default_concurrency + order_goods.additional_concurrency
                total_hours = {1: 1/24, 2: 1, 3: 7, 4: 30, 5: 90, 6: 365}.get(order_goods.product_package.time_limit) * 24 * order_goods.period
                creation_time = datetime.now()
                expiration_time = creation_time + timedelta(hours=total_hours)
                for i in range(order_goods.number):
                    service = Service(user=user, product=order_goods.product_package.product, concurrency=concurrency, creation_time=creation_time, expiration_time=expiration_time)
                    service.save()
            return Response('success')
        else:
            return Response('failure')
