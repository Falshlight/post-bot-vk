import vk
import re
import time
import city_list
import threading
import group_leave
import random
from service import captcha_handler

repost_code = """
var uid = %s;
var id = %s;
var w_id = "%s";
var l = API.likes.add({"v": "5.12", "type": "post", "owner_id": uid, "item_id": id});
var r = API.wall.repost({"object": w_id, "v": "5.12"});
return [l, r];"""


def add_log(text, t=1):
    log_path = "post_bot_log.txt"
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
            print(e)
            if e.code == 14:
                add_log('Preparing to captcha')
                key = captcha_handler(e.error_data['captcha_img'])
                sid = e.error_data['captcha_sid']
                return make_api_req(method, *args, **kwargs, captcha_sid=sid, captcha_key=key)
            if e.code == 15:
                cnt = 20
            cnt += 1
            time.sleep(cnt + 2)
            if cnt >= 20:
                add_log(str(e), 2)
                send_trouble(e)
                return


def send_trouble(e):
    api = vk.API(vk.Session())

    with open('at.txt') as f:
        at = f.read().strip()
    with open('owner_id.txt') as f:
        uid = f.read().strip()

    mes = "Unknown error. See the log file"
    wait_day = False
    run_group_leave = False
    send_message = True
    if e.code == 214:
        mes = "Был достигнут лимит в 50 постов/день"
        wait_day = True
    elif e.code == 14:
        send_message = False
    elif e.code == 103:
        mes = "Достигнут лимит групп. Запускаю скрипт дл удаления старых подписок"
        run_group_leave = True
    elif e.code == 15:
        send_message = False

    if send_message:
        make_api_req(api.messages.send, access_token=at, user_id=uid, message=mes)

    if wait_day:
        date = time.strptime(time.ctime())
        hour = date[3]
        hour = 24 - hour
        minute = hour * 60 - date[4]
        time.sleep(minute * 60)
    if run_group_leave:
        group = threading.Thread(target=group_leave.start_g)
        group.daemon = True
        group.start()
    if mes == "Unknown error. See the log file":
        add_log(str(e), 2)
    del api


def start_p():
    add_log('Initialized')

    def get_posts(offset):
        res = make_api_req(api.newsfeed.search, q='репост розыгрыш', access_token=at, count=3, offset=offset)['items']
        return res

    def city_in_name(obj):
        name = make_api_req(api.groups.getById, group_id=abs(obj['owner_id']), access_token=at)[0]['name']
        name = name.lower()
        cit_list = city_list.get_list()
        lst = cit_list.lower()
        lst = lst.split("\n")
        for i in lst:
            i = i.strip()
            if i and i in name:
                add_log('Word %s found in %s' % (i, name))
                return True
        return False

    s = vk.Session()
    api = vk.API(s)

    with open('at.txt') as f:
        at = f.read().strip()

    times = 0
    psts = 0
    offset = 0
    while True:
        wait = True
        posts = get_posts(offset)
        session_posts = []
        for i in posts:
            print(i)
            time.sleep(1.5)
            if i['post_type'] == 'post' and i['owner_id'] < 0 and not city_in_name(i) and i not in session_posts:
                session_posts.append(i)
                offset = 0
                psts += 1
                w_id = 'wall%s_%s' % (i['owner_id'], i['id'])
                txt = i['text'].lower()
                key_words_groups = ['подписка', 'вступить', 'состоять', 'подписаться', 'быть участником', 'вступит',
                                    'быть подписчиком', 'подписываемся', 'быть подписанным']
                key_words_comment_cnt = ['порядковый номер', 'порядковым номером']

                r = make_api_req(api.execute, code=repost_code % (i['owner_id'], i['id'], w_id), access_token=at)
                if not r[0] and not r[1]:
                    continue
                add_log('Reposted %s' % w_id)

                for word in key_words_groups:
                    if word in txt:
                        make_api_req(api.groups.join, group_id=abs(i['owner_id']), access_token=at)
                        break

                for word in key_words_comment_cnt:
                    if word in txt:
                        comments = make_api_req(api.wall.getComments, access_token=at, owner_id=abs(i["owner_id"]) * -1,
                                                post_id=i['id'], sort="desc")['items']
                        if len(comments) == 0:
                            make_api_req(api.wall.createComment, access_token=at, message="1",
                                                   owner_id=abs(i["owner_id"]) * -1, post_id=i['id'])
                            add_log("Created '1' comment")
                        else:
                            for comment in comments:
                                mes = re.sub(r'[^\d]', '', comment['text'])
                                if mes and mes.isdigit():
                                    mes = str(int(mes) + 1)
                                    break
                            make_api_req(api.wall.createComment, access_token=at, message=mes,
                                                    owner_id=abs(i["owner_id"]) * -1, post_id=i['id'])
                            add_log('Created \'%s\' comment' % mes)
                        break
        if psts == 0:
            wait = False
        else:
            psts = 0
        if not wait:
            add_log('researching')
            offset += 3
        else:
            times += 1
            print(times)
            time.sleep(1000)
