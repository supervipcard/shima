from django.contrib.auth.models import AbstractUser
from django.db import models


class UserProfile(AbstractUser):
    """
    用户信息
    """
    phone = models.CharField(verbose_name="手机", max_length=11, unique=True)
    image = models.ImageField(verbose_name="头像", upload_to='head', default='head/default.png')

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


class Captcha(models.Model):
    """
    字母数字验证码
    """
    code_text = models.CharField("验证码文本", max_length=4)
    code_id = models.CharField("验证码ID", max_length=36)
    add_time = models.DateTimeField("添加时间", auto_now_add=True)

    class Meta:
        verbose_name = "字母数字验证码"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code_id


class EmailCode(models.Model):
    """
    邮箱验证码
    """
    email = models.EmailField("邮箱")
    code_text = models.CharField("验证码文本", max_length=4)
    add_time = models.DateTimeField("添加时间", auto_now_add=True)

    class Meta:
        verbose_name = "邮箱验证码"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.email
