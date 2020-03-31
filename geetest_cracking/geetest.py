"""
gettype:
    {'user_error': '网络不给力', 'status': 'error', 'error': 'illegal captcha_id', 'error_code': 'error_32'}  # gt格式不对
    {'error_code': 'error_34', 'status': 'error', 'user_error': '网络不给力', 'error': 'captcha not found'}  # gt找不到
get_and_ajax/api_get：
    {'status': 'error', 'user_error': '网络不给力', 'error_code': 'error_23', 'error': 'illegal challenge'}  # challenge格式不对
    {'error_code': 'error_21', 'user_error': '网络不给力', 'error': 'not proof', 'status': 'error'}  # challenge找不到
    {'error': 'old challenge', 'status': 'error', 'user_error': '网络不给力', 'error_code': 'error_02'}  # challenge已使用
gt_judgement:
    {'user_error': 'network error', 'error': 'illegal deepknow_id', 'status': 'error', 'error_code': '20002'}  # gt格式不对
    {'error_code': '20003', 'user_error': 'network error', 'error': 'scene not found', 'status': 'error'}  # gt找不到
"""
import itertools
import requests
import logging
import execjs
import time
import json
from PIL import Image
from io import BytesIO
import random
from retrying import retry
from geetest_cracking.image_handle import ImageHandler
from geetest_cracking.yolo import YOLO

logger = logging.getLogger('geetest')


class ForbiddenException(Exception):
    pass


class ChallengeUsedException(Exception):
    pass


class GtNotFoundException(Exception):
    pass


class ChallengeNotFoundException(Exception):
    pass


class UnKnownException(Exception):
    pass


class GeetestCrack:
    yolo = YOLO()

    with open('geetest_cracking/sense.js', 'r', encoding='utf-8') as f:
        source_sense = f.read()

    with open('geetest_cracking/fullpage.js', 'r', encoding='utf-8') as f:
        source_fullpage = f.read()

    with open('geetest_cracking/fullpage2.js', 'r', encoding='utf-8') as f:
        source_fullpage2 = f.read()

    with open('geetest_cracking/slide.js', 'r', encoding='utf-8') as f:
        source_slide = f.read()

    with open('geetest_cracking/click.js', 'r', encoding='utf-8') as f:
        source_click = f.read()

    def __init__(self, challenge, gt, referer):
        self.challenge = challenge
        self.gt = gt
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'
        self.session.headers['Referer'] = referer
        self.node = execjs.get('Node')

    def start(self):
        try:
            if self.challenge:
                if self.gettype():
                    self.get_and_ajax()
            else:
                judge_result = self.gt_judgement()
                self.challenge = judge_result['challenge']
                if judge_result['result'] == 'success':
                    return {'code': 0, 'message': '识别成功', 'data': {'challenge': self.challenge}}
                else:
                    pass

            api_get_result = self.api_get()
            if 'bg' in api_get_result and 'fullbg' in api_get_result:
                self.challenge = api_get_result['challenge']  # 滑动验证码获取图片之后challenge的值会改变
                slider_x = self.get_pos(api_get_result['bg'], api_get_result['fullbg'])
                # time.sleep(1)
                validate = self.api_ajax(slider_x, api_get_result)
                if validate:
                    return {'code': 0, 'message': '识别成功', 'data': {'validate': validate, 'challenge': self.challenge}}
                return {'code': 1014, 'message': '识别失败'}
            else:
                pic_type = api_get_result['data']['pic_type']  # 点选验证码类型（文字、图标、空间推理等）
                if pic_type == 'word':
                    coord = self.get_coord(api_get_result['data']['pic'])
                    time.sleep(1)
                    for points in itertools.permutations(coord, len(coord)):
                        coord = ','.join([str(i[0]) + '_' + str(i[1]) for i in points])
                        validate = self.api_ajax_click(coord, api_get_result['data'])
                        if validate:
                            return {'code': 0, 'message': '识别成功', 'data': {'validate': validate, 'challenge': self.challenge}}
                        break
                    return {'code': 1014, 'message': '识别失败'}
                else:
                    return {'code': 1020, 'message': '目前暂不支持{}类型验证码'.format(pic_type)}

        except GtNotFoundException:
            return {'code': 1011, 'message': 'gt值异常，请检查是否获取正确'}
        except ChallengeNotFoundException:
            return {'code': 1012, 'message': 'challenge值异常，请检查是否获取正确'}
        except ChallengeUsedException:
            return {'code': 1013, 'message': 'challenge重复提交，请重新获取'}
        except UnKnownException:
            logger.exception('')
            return {'code': 1015, 'message': '极验识别服务异常'}
        except:
            logger.exception('')
            return {'code': 1015, 'message': '极验识别服务异常'}

    def gt_judgement(self):
        """若challenge不是由目标网站生成，则是由极验通过目标网站的gt值生成（例如拉勾、斗鱼）"""
        context = self.node.compile(self.source_sense)
        data = context.call('outside_link', self.gt)
        url = 'https://api.geetest.com/gt_judgement?pt=0&gt={}'.format(self.gt)
        response = requests.post(url=url, data=data)
        result = json.loads(response.text)
        if result.get('status') == 'error':
            if result.get('error_code') in ['20002', '20003']:
                raise GtNotFoundException
            else:
                raise UnKnownException(result)
        return result

    def gettype(self):
        """判断是否需要点击验证按钮"""
        url = 'https://api.geetest.com/gettype.php?gt={gt}&callback=geetest_{t}'.format(gt=self.gt,
                                                                                        t=int(time.time() * 1000))
        response = self.session.get(url=url)
        result = json.loads(response.text[22: -1])
        if result.get('status') == 'error':
            if result.get('error_code') in ['error_32', 'error_34']:
                raise GtNotFoundException
            else:
                raise UnKnownException(result)
        return result['data']['type'] == 'fullpage'

    def get_and_ajax(self):
        """点击验证按钮"""
        context = self.node.compile(self.source_fullpage)
        E, w_get = context.call('outside_link', self.challenge, self.gt)

        get_url = 'https://api.geetest.com/get.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w_get, t=int(time.time() * 1000))
        get_response = self.session.get(url=get_url)
        result = json.loads(get_response.text[22: -1])
        if result.get('status') == 'error':
            if result.get('error_code') in ['error_21', 'error_23']:
                raise ChallengeNotFoundException
            elif result.get('error_code') == 'error_02':
                raise ChallengeUsedException
            else:
                raise UnKnownException(result)

        context = self.node.compile(self.source_fullpage2)
        w_ajax = context.call('outside_link', self.challenge, self.gt, E, result['data'])

        ajax_url = 'https://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w_ajax, t=int(time.time() * 1000))
        ajax_response = self.session.get(url=ajax_url)
        result = json.loads(ajax_response.text[22: -1])
        if result.get('status') == 'error':
            raise UnKnownException(result)

    def api_get(self):
        """获取图片"""
        url = 'https://api.geetest.com/get.php'
        params = {
            'is_next': 'true',
            'type': '',
            'gt': self.gt,
            'challenge': self.challenge,
            'lang': 'zh-cn',
            'https': 'true',
            'protocol': 'https://',
            'offline': 'false',
            'product': '',
            'api_server': 'api.geetest.com',
            'width': '100%',
            'callback': 'geetest_{}'.format(int(time.time() * 1000)),
        }
        response = self.session.get(url=url, params=params)
        result = json.loads(response.text[22: -1])
        if result.get('status') == 'error':
            if result.get('error_code') in ['error_21', 'error_23']:
                raise ChallengeNotFoundException
            elif result.get('error_code') == 'error_02':
                raise ChallengeUsedException
            else:
                raise UnKnownException(result)
        return result

    def api_ajax(self, x, data):
        """提交验证"""
        context = self.node.compile(self.source_slide)
        points = self.simulate(x)
        w = context.call('outside_link', x, points, data)

        url = 'https://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w, t=int(time.time() * 1000))
        response = self.session.get(url=url)
        result = json.loads(response.text[22: -1]) if response.text.startswith('geetest_') else json.loads(response.text)
        if result.get('validate'):
            return result['validate']

    def api_ajax_click(self, points, data):
        """提交验证"""
        getpass = self.node.compile(self.source_click)
        w = getpass.call('outside_link', self.challenge, self.gt, points, data)

        url = 'https://api.geetest.com/ajax.php?gt={gt}&challenge={challenge}&lang={lang}&w={w}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', w=w, t=int(time.time() * 1000))
        response = self.session.get(url=url)
        result = json.loads(response.text[22: -1])['data'] if response.text.startswith('geetest_') else json.loads(response.text)
        if result.get('validate'):
            return result['validate']

    def refresh(self):
        """刷新"""
        url = 'https://api.geetest.com/refresh.php?gt={gt}&challenge={challenge}&lang={lang}&type={type}&callback=geetest_{t}'.format(
            gt=self.gt, challenge=self.challenge, lang='zh-cn', type='', t=int(time.time() * 1000))
        response = self.session.get(url=url)
        result = json.loads(response.text[22: -1]) if response.text.startswith('geetest_') else json.loads(response.text)
        return result

    def get_pos(self, bg, fullbg):
        """获取图片缺口坐标"""
        bg_url = 'https://static.geetest.com/' + bg
        bg_response = self.session.get(url=bg_url)
        bg_image = Image.open(BytesIO(bg_response.content))

        fullbg_url = 'https://static.geetest.com/' + fullbg
        fullbg_response = self.session.get(url=fullbg_url)
        fullbg_image = Image.open(BytesIO(fullbg_response.content))

        pos = ImageHandler.subtract(bg_image, fullbg_image)
        return pos

    @staticmethod
    def simulate(pos):
        """模拟滑动轨迹"""
        points = list()
        points.append([0, 0, 0])
        x = 0
        t = random.randint(50, 80)
        while abs(x - pos) > 10:
            x += random.randint(1, 5)
            t += random.randint(15, 30)
            points.append([int(x), 0, int(t)])

        while abs(x - pos) <= 10:
            x += random.randint(0, 1)
            t += random.randint(15, 30)
            points.append([int(x), 0, int(t)])
            if x == pos:
                break

        t += random.randint(200, 300)
        points.append([int(x), 0, int(t)])
        return points

    def get_coord(self, bg):
        """获取图片汉字坐标"""
        bg_url = 'https://static.geetest.com/' + bg
        bg_response = self.session.get(url=bg_url)
        bg_image = Image.open(BytesIO(bg_response.content))
        bg_image = bg_image.crop((0, 0, 344, 344))
        # bg_image.save('a.jpg')

        out_boxes = self.yolo.detect_image(bg_image)
        out_boxes = out_boxes.tolist()

        lis = list()
        for box in out_boxes:
            x = int((box[1] + box[3]) / 2 / 344 * 10000)
            y = int((box[0] + box[2]) / 2 / 344 * 10000)
            lis.append((x, y))
        return lis
