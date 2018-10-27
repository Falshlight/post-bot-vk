import post_bot
import win_control_bot
import threading


post = threading.Thread(target=post_bot.start_p)
win = threading.Thread(target=win_control_bot.start_w)
#post.daemon = True
#win.daemon = True


post.start()
win.start()