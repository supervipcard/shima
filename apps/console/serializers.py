import time
import random
from datetime import datetime, timedelta
from rest_framework import serializers

from .models import *
from utils.alipay_ import Alipay


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductPackageSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = ProductPackage
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    pay_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    goods = serializers.SerializerMethodField()
    order_url = serializers.SerializerMethodField()

    def get_goods(self, obj):
        order_goods = OrderGoods.objects.filter(order__order_id=obj.order_id)
        if order_goods:
            result = OrderGoodsSerializer(order_goods[0], many=False, context={'request': self.context['request']}).data
            return result

    def get_order_url(self, obj):
        order_url = Alipay.pay('测试', obj.order_id, obj.amount) if obj.pay_status == 1 else None
        return order_url

    class Meta:
        model = Order
        fields = '__all__'


class OrderPurchaseSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    order = OrderSerializer(read_only=True)
    product_package = ProductPackageSerializer(read_only=True)

    # 表单字段
    product_package_id = serializers.IntegerField(label='产品套餐包ID', write_only=True,
                                                  error_messages={
                                                      'required': '套餐包ID不能为空',
                                                      'invalid': '套餐包ID不合法',
                                                  })
    period = serializers.IntegerField(label='新购周期', default=1, min_value=1, max_value=24,
                                      error_messages={
                                          'max_value': '新购周期必须小于等于24',
                                          'min_value': '新购周期必须大于等于1'
                                      })
    number = serializers.IntegerField(label='新购数量', default=1, min_value=1, max_value=999,
                                      error_messages={
                                          'max_value': '新购数量必须小于等于999',
                                          'min_value': '新购数量必须大于等于1'
                                      })
    additional_concurrency = serializers.IntegerField(label='额外每秒请求数', default=0, min_value=0, max_value=100,
                                                      error_messages={
                                                          'max_value': '额外每秒请求数必须小于等于100',
                                                          'min_value': '额外每秒请求数必须大于等于1'
                                                      })

    def validate(self, attrs):
        product_package_id = attrs['product_package_id']
        del attrs['product_package_id']
        try:
            attrs['product_package'] = ProductPackage.objects.get(id=product_package_id)
        except ProductPackage.DoesNotExist:
            raise serializers.ValidationError("套餐包不存在")
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        order_id = "{time_str}{userid}{ranstr}".format(time_str=time.strftime("%Y%m%d%H%M%S"), userid=user.id, ranstr=random.randint(10000, 99999))
        amount = (validated_data['product_package'].price + validated_data['product_package'].additional_concurrency_price * validated_data['additional_concurrency']) * validated_data['period'] * validated_data['number']
        order = Order(user=user, order_id=order_id, amount=amount, transaction_type=2)
        order.save()
        validated_data['order'] = order
        instance = super(OrderPurchaseSerializer, self).create(validated_data=validated_data)
        return instance

    class Meta:
        model = OrderGoods
        fields = '__all__'


class OrderGoodsSerializer(serializers.ModelSerializer):
    product_package = serializers.StringRelatedField()

    class Meta:
        model = OrderGoods
        exclude = ('order',)


class ServiceSerializer(serializers.ModelSerializer):
    creation_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    expiration_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    renewal_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    is_expired = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()

    def get_is_expired(self, obj):
        is_expired = datetime.now() >= obj.expiration_time
        return is_expired

    def get_remaining_days(self, obj):
        remaining_days = (obj.expiration_time - datetime.now()).days
        return remaining_days

    class Meta:
        model = Service
        fields = '__all__'
