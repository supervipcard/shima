import re
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()
redis_client = get_redis_connection("default")


class SMSCodeSerializer(serializers.Serializer):
    """
    发送短信验证码
    """
    phone = serializers.RegexField(
        label='手机号码', regex='^\d{11}$'
    )


class UserRegSerializer(serializers.ModelSerializer):
    """
    用户注册
    """
    phone = serializers.CharField(label='手机号码', validators=[RegexValidator(regex='^\d{11}$', message='手机号码格式不正确'), UniqueValidator(queryset=User.objects.all(), message='手机号码已注册')],
                                  error_messages={
                                      'required': '手机号码不能为空',
                                      'blank': '手机号码不能为空',
                                  })
    password = serializers.CharField(style={'input_type': 'password'}, label='密码', min_length=6, max_length=18, write_only=True,
                                     error_messages={
                                         'required': '密码不能为空',
                                         'blank': '密码不能为空',
                                         'max_length': '密码格式不正确',
                                         'min_length': '密码格式不正确'
                                     })
    sms_code = serializers.CharField(label='短信验证码', write_only=True,
                                     error_messages={
                                         'required': '短信验证码不能为空',
                                         'blank': '短信验证码不能为空'
                                     })

    def validate_sms_code(self, sms_code):
        key = 'smscode:{}'.format(self.initial_data.get('phone'))
        val = redis_client.get(key)
        if not val or val.decode('utf8').lower() != sms_code.lower():
            raise serializers.ValidationError("短信验证码错误")
        return sms_code

    def validate(self, attrs):
        del attrs['sms_code']
        return attrs

    def create(self, validated_data):
        user = super(UserRegSerializer, self).create(validated_data=validated_data)  # 这一步会往数据库添加数据
        user.set_password(validated_data["password"])  # 密码加密
        user.save()  # 保存
        return user

    class Meta:
        model = User
        fields = ("phone", "username", "password", "sms_code")  # 进行验证和序列化的字段，post的数据中不在fields中的字段会忽略，字段来源是当前类的Field和models的Field
        extra_kwargs = {
            'username': {'error_messages': {'required': '用户名不能为空', 'blank': '用户名不能为空', 'max_length': '用户名格式不正确', 'min_length': '用户名格式不正确'}}
        }


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户信息
    """
    class Meta:
        model = User
        fields = ("phone", "username", "email", "avatar", "date_joined")


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    用户信息修改
    """
    password = serializers.CharField(
        style={'input_type': 'password'}, label='密码', min_length=6, max_length=18, write_only=True, required=False
    )

    def update(self, instance, validated_data):
        user = super(UserUpdateSerializer, self).update(instance=instance, validated_data=validated_data)
        if validated_data.get('password'):
            user.set_password(validated_data["password"])
            user.save()
        return user

    class Meta:
        model = User
        fields = ("email", "password")
