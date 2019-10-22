"""
开启键空间通知：redis-cli config set notify-keyspace-events KEx
"""
import re
from django_redis import get_redis_connection
from .models import *
from .alipay_utils import AliPayModule


def callback(msg):
    if msg.get('data') == b'expired':
        channel = msg.get('channel').decode('utf8')
        order_id = re.search(r'ids:(.*)$', channel).group(1)
        order = Order.objects.get(order_id=order_id)
        order.pay_status = 3
        order.save()
        AliPayModule.close(order_id)


class TimeoutController:
    def __init__(self):
        self.rs = get_redis_connection("default")
        pubsub = self.rs.pubsub()
        pubsub.psubscribe(**{'__keyspace@*__:ids:*': callback})
        pubsub.run_in_thread(sleep_time=1, daemon=True)

    def countdown(self, order_id):
        redis_key = 'ids:{}'.format(order_id)
        self.rs.set(redis_key, '')
        self.rs.expire(redis_key, 1800)

    def delete(self, order_id):
        redis_key = 'ids:{}'.format(order_id)
        self.rs.delete(redis_key)
