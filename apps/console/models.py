import os
import base64
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Product(models.Model):
    """
    产品
    """
    name = models.CharField(verbose_name='产品名称', max_length=10)  # 极验识别、易盾识别
    doc_url = models.URLField(verbose_name='接口文档链接地址', null=True, blank=True)
    is_open = models.BooleanField(verbose_name='是否开放', default=True)

    class Meta:
        verbose_name = "产品"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ProductPackage(models.Model):
    """
    产品套餐包
    """
    time_limit_choices = (
        (1, "时"),
        (2, "日"),
        (3, "周"),
        (4, "月"),
        (5, "季"),
        (6, "年"),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='产品')
    time_limit = models.SmallIntegerField(verbose_name='套餐期限', choices=time_limit_choices)
    price = models.FloatField(verbose_name='套餐单价')
    default_concurrency = models.IntegerField(verbose_name='默认每秒请求数')
    additional_concurrency_price = models.FloatField(verbose_name='额外每秒请求数单价')

    class Meta:
        verbose_name = "产品套餐包"
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}{}包'.format(self.product, dict(self.time_limit_choices)[self.time_limit])


class Order(models.Model):
    """
    订单
    """
    transaction_type_choices = (
        (1, "充值"),
        (2, "新购"),
        (3, "续费"),
        (4, "升级"),
    )

    pay_channel_choices = (
        (1, "钱包"),
        (2, "支付宝"),
        (3, "微信"),
    )

    pay_status_choices = (
        (1, "待支付"),
        (2, "已完成"),
        (3, "超时未支付"),
        (4, "已取消"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    order_id = models.CharField(verbose_name='订单编号', max_length=30, primary_key=True)
    trade_no = models.CharField(verbose_name="支付宝交易号", max_length=100, unique=True, null=True, blank=True)
    transaction_type = models.SmallIntegerField(verbose_name='交易类型', choices=transaction_type_choices)
    amount = models.FloatField(verbose_name="订单金额")
    pay_channel = models.SmallIntegerField(verbose_name='支付渠道', choices=pay_channel_choices, null=True, blank=True)
    pay_status = models.SmallIntegerField(verbose_name="订单状态", choices=pay_status_choices, default=1)
    pay_time = models.DateTimeField(verbose_name='支付时间', null=True, blank=True)
    add_time = models.DateTimeField(verbose_name='下单时间', auto_now_add=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_id


class OrderGoods(models.Model):
    """
    新购订单内的商品详情
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='订单')
    product_package = models.ForeignKey(ProductPackage, on_delete=models.CASCADE, verbose_name='产品套餐包')
    period = models.IntegerField(verbose_name='新购周期', default=1)
    number = models.IntegerField(verbose_name='新购数量', default=1)
    additional_concurrency = models.IntegerField(verbose_name='额外每秒请求数', default=0)

    class Meta:
        verbose_name = "新购订单内的商品详情"
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.order)


def generate_access_token():
    return base64.b64encode(os.urandom(48)).decode('utf-8')


class Service(models.Model):
    """
    已购买的服务
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='产品')
    access_token = models.CharField(verbose_name='通行秘钥', max_length=64, default=generate_access_token, unique=True)
    concurrency = models.IntegerField(verbose_name='每秒请求数')
    creation_time = models.DateTimeField(verbose_name='创建时间')
    expiration_time = models.DateTimeField(verbose_name='到期时间')
    renewal_time = models.DateTimeField(verbose_name='续费时间', null=True, blank=True)

    class Meta:
        verbose_name = "已购买的服务"
        verbose_name_plural = verbose_name
