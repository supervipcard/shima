from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserProfile(AbstractUser):
    """
    用户信息
    """
    username_validator = UnicodeUsernameValidator(message='用户名格式不正确')

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': '用户名已注册',
        },
    )
    phone = models.CharField(verbose_name="手机号码", max_length=11, unique=True)
    avatar = models.ImageField(verbose_name="头像", upload_to='avatar', default='avatar/default.png')

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
