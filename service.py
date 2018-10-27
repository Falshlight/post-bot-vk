import time
import random
import vk, vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


def captcha_handler(img):
    s = vk.Session()
    api = vk.API(s)

    with open('at.txt') as f:
        at = f.read().strip()

    k = ""
    for i in range(3): k += str(random.randint(0, 10))
    mes = "Пожалуйста, введите капчу:\n%s\nУникальный ключ: %s\nОтвет введите в таком формате: <уникальный_ключ>=<капча>\n\"<\" вводить не нужно" % \
          (img, k)

    with open('owner_id.txt') as f:
        uid = f.read().strip()

    make_api_req(api.messages.send, access_token=at, message=mes, user_id=uid)
    vk_session = vk_api.VkApi(token=at)
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.user_id == uid and '=' in event.text:
                mk, captcha = event.text.split('=')
                if mk == k:
                    add_log('Captcha key:', captcha)
                    return captcha


def make_api_req(method, *args, **kwargs):
    cnt = 0
    while True:
        try:
            return method(*args, **kwargs, v=5.71)
        except Exception as e:
            if e.code == 14:
                key = captcha_handler(e.error_data['captcha_img'])
                sid = e.error_data['captcha_sid']
                return make_api_req(method, *args, **kwargs, captcha_sid=sid, captcha_key=key)
            cnt += 1
            time.sleep(cnt + 2)
            if cnt == 30:
                add_log(str(e), 2)
                return


def add_log(text, t=1):
    log_path = "service_log.txt"
    td = time.ctime()
    prefix = "INFO"
    if t == 2: prefix = "ERROR"
    s = "[%s] [%s]: %s\n" % (prefix, td, text)
    with open(log_path, 'a', encoding="utf-8") as f:
        f.write(s)
