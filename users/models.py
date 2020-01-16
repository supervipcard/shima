from django.contrib.auth.models import AbstractUser
from django.db import models


class UserProfile(AbstractUser):
    """
    用户信息
    """
    phone = models.CharField(verbose_name="手机号码", max_length=11, unique=True)
    avatar = models.ImageField(verbose_name="头像", upload_to='avatar', default='avatar/default.png')

    class Meta:
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Wallet(models.Model):
    """
    钱包
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name='用户')
    balance = models.FloatField(verbose_name='余额', default=0.0)
    consumption_amount = models.FloatField(verbose_name='累积消费', default=0.0)

    class Meta:
        verbose_name = "钱包"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user
