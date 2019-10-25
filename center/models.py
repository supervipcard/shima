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

    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='产品')
    time_limit = models.SmallIntegerField(verbose_name='套餐期限', choices=time_limit_choices)
    price = models.FloatField(verbose_name='套餐单价')
    default_concurrency = models.IntegerField(verbose_name='默认并发数', default=5)
    additional_concurrency_price = models.FloatField(verbose_name='额外并发单价')

    def __str__(self):
        return '基础（{price}元 / {time_limit}） + 额外每秒请求数（{additional_concurrency_price}元 / {time_limit}）'.format(
            price=self.price, additional_concurrency_price=self.additional_concurrency_price, time_limit=dict(self.time_limit_choices)[self.time_limit])


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
    # product_type = models.CharField(verbose_name='产品类型', max_length=10)
    amount = models.FloatField(verbose_name="订单金额")
    pay_channel = models.SmallIntegerField(verbose_name='支付渠道', choices=pay_channel_choices, default=2)
    pay_status = models.SmallIntegerField(verbose_name="订单状态", choices=pay_status_choices, default=1)
    pay_time = models.DateTimeField(verbose_name='支付时间', null=True, blank=True)
    add_time = models.DateTimeField(verbose_name='下单时间', auto_now_add=True)


def generate_access_token():
    return base64.b64encode(os.urandom(48)).decode('utf-8')


class InterfaceChannel(models.Model):
    """
    产品接口通道
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='产品')
    access_token = models.CharField(verbose_name='通行秘钥', max_length=64, default=generate_access_token)
    concurrency = models.IntegerField(verbose_name='并发数')
    creation_time = models.DateTimeField(verbose_name='创建时间')
    expiration_time = models.DateTimeField(verbose_name='到期时间')
    renewal_time = models.DateTimeField(verbose_name='续费时间', null=True, blank=True)


class OrderProduct(models.Model):
    """
    订单内的产品详情
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='订单')
    product_package = models.ForeignKey(ProductPackage, on_delete=models.PROTECT, verbose_name='产品套餐包', null=True, blank=True)
    channel = models.ForeignKey(InterfaceChannel, on_delete=models.PROTECT, verbose_name='接口通道', null=True, blank=True)
    period = models.IntegerField(verbose_name='新购/续费周期', null=True, blank=True)
    number = models.IntegerField(verbose_name='新购数量', null=True, blank=True)
    additional_concurrency = models.IntegerField(verbose_name='新购额外并发数', null=True, blank=True)
    new_additional_concurrency = models.IntegerField(verbose_name='升级新增并发数', null=True, blank=True)
