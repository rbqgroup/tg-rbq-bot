import time
import telepot # 將 telepot 這個模組匯入到 Python 中來
from telepot.loop import MessageLoop
from pprint import pprint

bot = telepot.Bot('*** API ***') # 將bot這個在程式中使用的 variable 和你的 bot token 聯絡起來，在之後的程式中，每當要命令bot的時候可以直接 call bot 的 instance
me = bot.getMe() # 在這裡你的bot的資訊將以一個 dictionary 的形式被 print 出來
pprint(me)

# 接收訊息：設計上， telegram bot 是無法主動向使用者傳送訊息的（主要的目的是防止 spam )，所以你需要主動地透過指令以獲取使用者的資訊：
response = bot.getUpdates()
pprint(response)

bot.sendMessage(-1, "复活") # -1:聊天ID 傳送訊息
