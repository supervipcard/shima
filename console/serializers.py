from rest_framework import serializers
from .models import *


class OrderListSerializer(serializers.ModelSerializer):
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Order
        fields = '__all__'


class ChannelSerializer(serializers.ModelSerializer):
    creation_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    expiration_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    renewal_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = InterfaceChannel
        fields = '__all__'
