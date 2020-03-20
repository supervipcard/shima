import re
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_jwt.serializers import JSONWebTokenSerializer, authenticate, jwt_payload_handler, jwt_encode_handler

User = get_user_model()
redis_client = get_redis_connection("default")


class SMSCodeSerializer(serializers.Serializer):
    """
    发送短信验证码
    """
    phone = serializers.RegexField(
        label='手机号码', regex='^\d{11}$', error_messages={'invalid': '手机号码格式不正确'}
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
    password = serializers.CharField(style={'input_type': 'password'}, label='密码', min_length=6, max_length=32, write_only=True,
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

    def validate(self, attrs):
        key = 'smscode:{}'.format(attrs['phone'])
        val = redis_client.get(key)
        if not val or val.decode('utf8').lower() != attrs['sms_code'].lower():
            raise serializers.ValidationError("短信验证码错误")
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
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = User
        fields = ("phone", "username", "qq", "gender", "avatar", "date_joined")


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    用户信息修改
    """
    class Meta:
        model = User
        fields = ("qq", "gender", "avatar")
        extra_kwargs = {
            'qq': {'error_messages': {'max_length': 'QQ号格式不正确'}},
            'gender': {'error_messages': {'invalid_choice': '性别参数异常'}}
        }


class ChangePasswordSerializer(serializers.Serializer):
    """
    密码修改
    """
    old_password = serializers.CharField(style={'input_type': 'password'}, label='旧密码', min_length=6, max_length=32,
                                         error_messages={
                                             'required': '旧密码不能为空',
                                             'blank': '旧密码不能为空',
                                             'max_length': '旧密码格式不正确',
                                             'min_length': '旧密码格式不正确'
                                         })
    new_password = serializers.CharField(style={'input_type': 'password'}, label='新密码', min_length=6, max_length=32,
                                         error_messages={
                                             'required': '新密码不能为空',
                                             'blank': '新密码不能为空',
                                             'max_length': '新密码格式不正确',
                                             'min_length': '新密码格式不正确'
                                         })

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError("旧密码错误")
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """
    密码重置
    """
    phone = serializers.CharField(label='手机号码', validators=[RegexValidator(regex='^\d{11}$', message='手机号码格式不正确')],
                                  error_messages={
                                      'required': '手机号码不能为空',
                                      'blank': '手机号码不能为空',
                                  })
    new_password = serializers.CharField(style={'input_type': 'password'}, label='新密码', min_length=6, max_length=32,
                                         error_messages={
                                             'required': '新密码不能为空',
                                             'blank': '新密码不能为空',
                                             'max_length': '新密码格式不正确',
                                             'min_length': '新密码格式不正确'
                                         })
    sms_code = serializers.CharField(label='短信验证码', write_only=True,
                                     error_messages={
                                         'required': '短信验证码不能为空',
                                         'blank': '短信验证码不能为空'
                                     })

    def validate_phone(self, phone):
        try:
            User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("手机号码未注册")
        return phone

    def validate(self, attrs):
        key = 'smscode:{}'.format(attrs['phone'])
        val = redis_client.get(key)
        if not val or val.decode('utf8').lower() != attrs['sms_code'].lower():
            raise serializers.ValidationError("短信验证码错误")
        del attrs['sms_code']
        return attrs


class CustomJSONWebTokenSerializer(JSONWebTokenSerializer):
    def __init__(self, *args, **kwargs):
        super(CustomJSONWebTokenSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField(label='用户名/手机号码', max_length=32,
                                                                 error_messages={
                                                                     'required': '用户名/手机号码不能为空',
                                                                     'blank': '用户名/手机号码不能为空',
                                                                     'max_length': '用户名/手机号码格式不正确',
                                                                     'min_length': '用户名/手机号码格式不正确'
                                                                 })
        self.fields['password'] = serializers.CharField(style={'input_type': 'password'}, label='密码', min_length=6, max_length=32, write_only=True,
                                                        error_messages={
                                                            'required': '密码不能为空',
                                                            'blank': '密码不能为空',
                                                            'max_length': '密码格式不正确',
                                                            'min_length': '密码格式不正确'
                                                        })

    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }
        user = authenticate(**credentials)

        if user:
            if not user.is_active:
                msg = 'User account is disabled.'
                raise serializers.ValidationError(msg)

            payload = jwt_payload_handler(user)

            return {
                'token': jwt_encode_handler(payload),
                'user': user
            }
        else:
            msg = '用户名或密码错误'
            raise serializers.ValidationError(msg)
