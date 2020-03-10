import time
from alipay import AliPay
from shima.settings import appid, app_private_key_string, alipay_public_key_string, return_url


class Alipay:
    alipay = AliPay(
        appid=appid,
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True,  # True 表示沙箱环境
    )

    @classmethod
    def pay(cls, subject, out_trade_no, total_amount):
        # Pay via Web，open this url in your browser: https://openapi.alipay.com/gateway.do? + order_string
        order_string = cls.alipay.api_alipay_trade_page_pay(
            subject=subject,
            out_trade_no=out_trade_no,
            total_amount=total_amount,
            return_url=return_url,
            notify_url=return_url,
        )
        order_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return order_url

    @classmethod
    def verify(cls, data, signature):
        return cls.alipay.verify(data, signature)

    @classmethod
    def close(cls, out_trade_no):
        return cls.alipay.api_alipay_trade_close(out_trade_no=out_trade_no)


if __name__ == '__main__':
    order_id = time.strftime("%Y%m%d%H%M%S")
    print(order_id)
    print(Alipay.pay('测试', order_id, 0.01))
