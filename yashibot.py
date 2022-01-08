# -*- coding:utf-8 -*-
from telegram import Update
# pip uninstall python-telegram-bot telegram
# pip install python-telegram-bot --upgrade
# https://github.com/python-telegram-bot/python-telegram-bot/wiki
from telegram.ext import CallbackContext
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import redis
import json

print('正在初始化...')

c_TGTOKEN = '*:*'
c_REDIS = ['127.0.0.1', 6379, '*']
c_REDISDB = [10]  # 配置庫
c_CHAR = [['呜', '嘤', '哈', '啊', '唔', '嗯'], ['！', '？', '…']]

updater = Updater(token=c_TGTOKEN, use_context=True)
dispatcher = updater.dispatcher

# Redis
redis_pool = redis.ConnectionPool(
    host=c_REDIS[0], port=c_REDIS[1], password=c_REDIS[2], db=c_REDISDB[0])


def isPermission(chatID: int) -> bool:
    """檢查該會話是否有許可權使用此機器人"""
    redis_conn = redis.Redis(connection_pool=redis_pool)
    rediskey = 'can_' + str(chatID)
    isPass = redis_conn.get(rediskey)
    redis_conn.close()
    if isPass != None and isPass == b'1':
        return True
    print('不能提供服务 ' + str(chatID))
    return False


def start(update: Update, context: CallbackContext):
    """響應 /start"""
    fromUser: str = update.message.from_user.username
    text: str = '你好， '+fromUser+' ！这里是神楽坂小雅诗。我只为雅诗指定的群组提供服务。'
    print(text)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()


def echo(update: Update, context: CallbackContext):
    """回顯收到的所有非命令訊息"""


echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)


def gag(update: Update, context: CallbackContext):
    """為他人佩戴口球"""
    if isPermission(update.message.chat.id) == False:
        return
    toUser: str = context.args[0]
    if toUser[0] != '@':
        return
    fromUser: str = '@'+update.message.from_user.username
    chatID: int = update.message.chat.id
    redis_conn = redis.Redis(connection_pool=redis_pool)
    rediskey: str = 'gag_' + chatID + '_' + str(toUser)
    gagInfo: str = redis_conn.get(rediskey).decode()
    alert: str = ''
    if gagInfo != None and len(gagInfo) > 0:
        if gagInfo == '0':
            redis_conn.close()
            alert = toUser+'刚刚挣脱口塞球！请给对方 1 分钟的休息时间！'
            print(alert)
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=alert)
            return
        infoArr = json.loads(gagInfo)
        gagTotal: int = -1
        names: list[str] = []
        isRepeat = False
        for name in infoArr:
            if gagTotal < 0:
                gagTotal = int(name)
                continue
            if name == fromUser:
                isRepeat = True
            names.append(name)
        if isRepeat:
            alert = '抱歉， '+fromUser+' 。你已经为 '+toUser+' 佩戴过口球了，请在 '+toUser+' 挣脱后再试。'
        else:
            gagTotal += 5
            infoArr[0] = gagTotal
            infoArr.append(fromUser)
            gagInfo = json.dumps(infoArr)
            redis_conn.set(rediskey, gagInfo)
            redis_conn.close()
            alert = fromUser+' 加固了 '+toUser+' 的口塞球！'
        alert += ' '+toUser+' 目前佩戴着被 ' + \
            (' 、 '.join(names))+' 安装或加固的口塞球，还需要挣扎 '+str(gagTotal)+' 次才能把它挣脱！'
    else:
        infoArr = [5, fromUser]
        gagInfo = json.dumps(infoArr)
        redis_conn.set(rediskey, gagInfo)
        redis_conn.close()
        alert = fromUser+' 为 '+toUser+' 戴上了口塞球！ '+toUser+' 必须挣扎 5 次才能挣脱它！其他人可以继续用同样指令加固 '+toUser+' 的口塞球（但同一个人只能在对方挣脱后才能再次为对方佩戴或加固口塞球）。 ' + \
            toUser+' 现在只能在消息中发送以下文字「' + \
            ('、'.join(c_CHAR[0]))+'」和中文标点「' + \
            ('、'.join(c_CHAR[1]))+'」，每发送一条消息算作挣扎一次，包含其他字符的消息不能发送！'
    if fromUser == toUser:
        alert += '居然自己给自己戴口塞球，真是个可爱的绒布球呢！'
    print(alert)
    context.bot.send_message(chat_id=update.effective_chat.id, text=alert)


caps_handler = CommandHandler('gag', gag)
dispatcher.add_handler(caps_handler)

print('初始化完成。')
