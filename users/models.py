from django.contrib.auth.models import AbstractUser
from django.db import models


class UserProfile(AbstractUser):
    """
    用户信息
    """
    phone = models.CharField(verbose_name="手机", max_length=11, unique=True)
    # email = models.EmailField("邮箱", unique=True)
    # image = models.ImageField(verbose_name="头像", upload_to='head', default='head/default.png')


class Wallet(models.Model):
    """
    钱包
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name='用户')
    balance = models.FloatField(verbose_name='余额', default=0.0)
