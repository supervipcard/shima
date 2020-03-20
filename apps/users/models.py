from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class UserProfile(AbstractUser):
    """
    用户信息
    """
    gender_choices = (
        (1, "男"),
        (2, "女"),
    )
    username_validator = UnicodeUsernameValidator(message='用户名格式不正确')

    username = models.CharField(
        verbose_name="用户名",
        max_length=32,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': '用户名已注册',
        },
    )
    phone = models.CharField(verbose_name="手机号码", max_length=11, unique=True)
    qq = models.CharField(verbose_name="QQ", max_length=32, null=True, blank=True)
    gender = models.SmallIntegerField(verbose_name="性别", choices=gender_choices, null=True, blank=True)
    avatar = models.ImageField(verbose_name="头像", upload_to='avatar', default='avatar/default.png', null=True, blank=True)

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
