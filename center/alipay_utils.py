from alipay import AliPay


class AliPayModule:
    app_private_key_string = b'-----BEGIN PRIVATE KEY-----\nMIIEogIBAAKCAQEAgFP1owmNSZsgeeXgfaFbjZvumRKeyMXqo1fmOzeYqM24IFhbcR7MutTLlRby+3CMERWElNJnT2030gf0YoarULhT8AvVeRjLXcsfaG4tVWo3qxmg9iglfklP6KYXD/twVQQd5oooZb0ZGIWecTeNJ/H8nw6MHQSPVF1JBzz/KBKZig7w30XYvmsOKU/t723Gtckg6NFx7aCpqpsRkznB5IePxpMDwNU5KowW+Olbu6jFTxXKIHeyg5FqwTVgrEo6H1/+1A3uJk8m6EzqvKA0QOltXC7cMxGsZR/UjiNdBFhthdigKAHsICB0wEvzEiecLWmyc6V0Hy47JFTPIUnvuwIDAQABAoIBAC2CmRiK6Kpz816HocesE9XyuPlcWyeE2SO4ppPVsbQb0PLXowZJD/4qPVDQZLe7QFFGulA1FiJa73LzEz5l2Be2Zz44VCqwGl9XC/pzKGykUL3DRwxFTJau1UICtScb2sirvxblZFJAb8f8iyZHty21agvWkuYvmc0nkCCbBzpkbZcfzQJUIOR0KhtY6hjhTl53eQ9GL+LzSQuCa2E9pum26Bu+/y/xOy1HEjn9XMbn5czsmMbi9WLGSTyYLQhV0h4JKbCn5mjJfUgPiWgJ73mme/YjxSgFEbqov48uJWC2D/2XCVqWGsyMfThhsSZaTT55dQ5BdW2fxWZkkmeWq/ECgYEAvQIKByq8UQMfBnhkr+Q8Izs407jCzJZ8ieozLn802bHjsyFULIX0slkt/0Vc3+YhGdpFElHmi9/QET7xjTuPnFco7n42uNwNPP8SSFH9KZBm+ePGZg+98EXjH1qnmke6ZDos8/438OB+InUE0nANT/83oI0mgiA2QVpa2qfqmdUCgYEArdAEVrQmc7NmINqK6lA9WCRMrWywhlrfhofRqTCDcL22MSn1Yq+PfcfCmEBc+wbvC2JI0uiKzbYQp3trnVTPCEWzYIBLk3qXJLvRbe0IxwVMyt/4QMkufIbsO7CAcl2AfNHnjyezwsfkTRXp0UMNoqLU9UmqR61cFi7Cf71/G08CgYBG8vICuLcSDgLiceUR5bHxY7S0PUHafI7pUmG+DYAwS8d2oYcwY2R0YmeS0F3JqmA4jSeqddX+IZjAMImKA5aoEEvMItK119ycTf916FkI9izBlxANldEt1X4pceVCU7STFQd027PyFsMiehzCRc+pfNtLyFBxPlg/dgRu2eOFtQKBgFTYIPYN9GMwJF9PLtZYGsnG1mMlljnPbCNoczDKjK7g/GmdWLo2hq3YcCYP7RNgfBmrfW7usqrd/90xgwOG3ZTlKT2nAr1X7yWwRPgK5+j2rlit4aoGSpng5rnwW5L4D3ten1EjCT3Ag7IZS0yqFaLZJ2kg720Ts8rkQm9GmiBDAoGAcdeK9QFCaV4SNi4FwSSaRTHhaRCX0wi5C1A1IePw4n2rqKd6hnAteVft5+BPb49M9j4sgVY6TxmmMtA7WoHN6DHOEj67cF1IIOICAoYPcoFUjN1kDVtKd6q0hZ07i8NTbQTHyKllSCrDos1Dntc+OwxMK06vclU7guC/nLHMKuU=\n-----END PRIVATE KEY-----'
    alipay_public_key_string = b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlamukh+6R0goKs5UJAG7E4ByZ/1Z4uTcvnWYB+FdNjDLyBdYDWzjBYQpqUTGAa2M6Gm2ovIbr9BQI67PCzuUsutUF4L4JvsINwLaOFou8Iy7NnT1745TXgtFYmOjPFICj0++mMIbHAClRLJzwOMOP9eESBRm7pmYxsiEMTR2qlgRaqgTzQKr4zjvEHh/02MkU6HcacjsFv5Gchl866iXPJlkOSG8WeSCTXwi9YzvPaQsfAZP+iwh/lW5EjnTDBZOLeLdA3e4o3s8nj2KfYv92HmS6s1Ob6IvbFZLA3hqBvNCppNWyF1ZcjYQnmDiQlYCTpiJJu6jQhYEDUHUj6IKDwIDAQAB\n-----END PUBLIC KEY-----'

    alipay = AliPay(
        appid="2016101300679868",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True,  # True 表示沙箱环境
    )

    @classmethod
    def pay(cls, out_trade_no, total_amount):
        subject = "测试订单"

        # Pay via Web，open this url in your browser: https://openapi.alipay.com/gateway.do? + order_string
        order_string = cls.alipay.api_alipay_trade_page_pay(
            out_trade_no=out_trade_no,
            total_amount=total_amount,
            subject=subject,
            return_url="http://101.132.71.2:8000/alipay/return/",
            notify_url="http://101.132.71.2:8000/alipay/return/",
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
    print(AliPayModule.pay('201910117', 0.01))
