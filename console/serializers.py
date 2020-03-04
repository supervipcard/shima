import time
import random
from rest_framework import serializers
from .models import *


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ProductPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPackage
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    pay_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Order
        fields = '__all__'


class OrderPurchaseSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    order = OrderSerializer(read_only=True)
    product_package = ProductPackageSerializer(read_only=True)

    # 表单字段
    product_package_id = serializers.IntegerField(write_only=True)
    period = serializers.IntegerField(default=1, min_value=1, max_value=100)
    number = serializers.IntegerField(default=1, min_value=1, max_value=100)
    additional_concurrency = serializers.IntegerField(default=0, min_value=0, max_value=100)

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
    order = OrderSerializer()
    product_package = ProductPackageSerializer()

    class Meta:
        model = OrderGoods
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    creation_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    expiration_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    renewal_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Service
        fields = '__all__'
