import time
import vk
from service import captcha_handler


def add_log(text, t=1):
    log_path = "group_leave_log.txt"
    td = time.ctime()
    prefix = "INFO"
    if t == 2: prefix = "ERROR"
    s = "[%s] [%s]: %s\n" % (prefix, td, text)
    with open(log_path, 'a', encoding="utf-8") as f:
        f.write(s)


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
            if cnt == 20:
                add_log(str(e), 2)
                return


def start_g():

    add_log("Initialized group_leave bot!")
    s = vk.Session()
    api = vk.API(s)

    with open('at.txt') as f:
        at = f.read().strip()

    groups = api.groups.get(access_token=at, count=1000, offset=3000, v=5.71)['items']

    groups.reverse()

    c = 0
    for i in groups[1:]:
        res = make_api_req(api.groups.leave, access_token=at, group_id=i)
        if not res:
            break
        c += 1
        time.sleep(3)
    add_log("Left groups count: %s" % c)
    add_log("Exiting...")
