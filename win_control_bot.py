import vk
import time
from service import captcha_handler

def add_log(text, t=1):
    log_path = "win_control_log.txt"
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
            return method(*args, **kwargs, v=5.12)
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

def check_parts(parts, s):
    for part in parts:
        if part not in s:
            return False
    return True


def start_w():
    session = vk.Session()
    api = vk.API(session)

    add_log("Initialized win_control_bot!")

    with open('at.txt') as f:
        at = f.read().strip()

    database = ""
    name = 'София Малаева'
    name_parts = ['Софи',"Малаев"]
    while True:
        result = make_api_req(api.newsfeed.search, q=name, count=5, access_token=at)['items']
        for i in result:
            if str(i) not in database and check_parts(name_parts, str(i)):
                database += str(i)
                string = "wall" + str(i['owner_id']) + '_' + str(i['id'])
                res = make_api_req(api.messages.send, user_id=217009004, access_token=at, attachment=string)
                if not res:
                    add_log("Exiting", 2)
                    break
                time.sleep(2)
        time.sleep(3600)
