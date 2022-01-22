from telegram import Update
from telegram.ext import CallbackContext
import redis
import json

def chat(update: Update, context: CallbackContext, redisPool1: redis.ConnectionPool):
    """聊天參與"""
    # redisVal: [["txt","<username> 快穿！"],["txt","<username> 心动不如行动！"]]
    text: str = update.message.text
    fromUser: str = '@'+update.message.from_user.username
    redisConnect = redis.Redis(connection_pool=redisPool1)
    redisKeys: list[bytes] = redisConnect.keys()
    for redisKey in redisKeys:
        key: str = redisKey.decode()
        if key in text:
            replyInfo = redisConnect.get(key)
            if replyInfo != None and len(replyInfo) > 0:
                replyInfo = replyInfo.decode()
                replyInfoArr = json.loads(replyInfo)
                for replyItem in replyInfoArr:
                    if replyItem[0] == 'txt':
                        replyText: str = replyItem[1]
                        replyText = replyText.replace('<username>', fromUser)
                        print(fromUser+' : '+text+' -> '+replyText)
                        context.bot.send_message(
                            chat_id=update.effective_chat.id, text=replyText)
    redisConnect.close()
