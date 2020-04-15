import requests
import json
import time
from geetest_cracking.geetest import GeetestCrack


def bilibili_register():
    url = 'https://passport.bilibili.com/web/captcha/combine?plat=11'.format(int(time.time() * 1000))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }
    response = requests.get(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)['data']['result']
    return data['challenge'], data['gt'], data['key']


def tyc_register():
    url = 'https://www.tianyancha.com/verify/geetest.xhtml'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
        'Content-Type': 'application/json; charset=UTF-8',
    }
    response = requests.post(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)['data']
    return data['challenge'], data['gt']


def general_register_slide():
    url = 'https://www.geetest.com/demo/gt/register-slide-official?t={}'.format(int(time.time() * 1000))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }
    response = requests.get(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)
    return data['challenge'], data['gt']


def general_register_click():
    url = 'https://www.geetest.com/demo/gt/register-click-official?t={}'.format(int(time.time() * 1000))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    }
    response = requests.get(url=url, headers=headers)
    print(response.text)
    data = json.loads(response.text)
    return data['challenge'], data['gt']


def main():
    referer = "https://passport.bilibili.com/login"

    # challenge, gt, key = bilibili_register()
    # challenge, gt = tyc_register()
    # challenge, gt = general_register_slide()
    # challenge, gt = general_register_click()
    challenge, gt = None, '9e296fca9afdfa4703b9f4bee02820af'

    result = GeetestCrack(challenge, gt, referer).start()
    print(result)


if __name__ == '__main__':
    main()
