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
import d_chat
import d_gag

print('正在初始化...')

c_TGTOKEN = '*:*'
c_REDIS = ['127.0.0.1', 6379, '*']
c_REDISDB = [10, 11]  # 配置庫
c_CHAR: list[list[str]] = [['呜', '嘤', '哈', '啊', '唔', '嗯'], ['！', '？', '…']]
c_CHARALL: list[str] = c_CHAR[0] + c_CHAR[1]
c_GAGADD = [3, 5]  # 每次增加多少

updater = Updater(token=c_TGTOKEN, use_context=True)
dispatcher = updater.dispatcher

# Redis
redisPool0: redis.ConnectionPool = redis.ConnectionPool(
    host=c_REDIS[0], port=c_REDIS[1], password=c_REDIS[2], db=c_REDISDB[0])
redisPool1: redis.ConnectionPool = redis.ConnectionPool(
    host=c_REDIS[0], port=c_REDIS[1], password=c_REDIS[2], db=c_REDISDB[1])


def isPermission(chatID: int) -> bool:
    """檢查該會話是否有許可權使用此機器人"""
    redisConnect = redis.Redis(connection_pool=redisPool0)
    rediskey = 'can_' + str(chatID)
    isPass = redisConnect.get(rediskey)
    redisConnect.close()
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
    """收到的所有非命令文字訊息"""
    if update.message.chat == None or isPermission(update.message.chat.id) == False:
        return
    d_gag.chk(update, context, redisPool0, c_CHAR)
    d_chat.chat(update, context, redisPool1)


def new_member(update, context):
    """新成員加入"""
    if update.message.chat == None or isPermission(update.message.chat.id) == False:
        return
    # print(update.message.from_user.username)
    for member in update.message.new_chat_members:
        # member: {'username': 'kagura_miyabi', 'last_name': 'みやび', 'first_name': '神楽', 'id': 1000005900, 'is_bot': False}
        username = member.username
        # alert = ' 你好， @'+username+' ，欢迎加入 '+update.message.chat.title+' ！下面，请发送「/verify 我是绒布球」来完成加群验证。' # TODO
        alert = ' 你好， @'+username+' ，欢迎加入 '+update.message.chat.title+' ！'
        print(alert)
        context.bot.send_message(chat_id=update.effective_chat.id, text=alert)


echoHandler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echoHandler)
newMemberHandler = MessageHandler(
    Filters.status_update.new_chat_members, new_member)
updater.dispatcher.add_handler(newMemberHandler)


def gag(update: Update, context: CallbackContext):
    """為他人佩戴口球"""
    if update.message.chat == None or isPermission(update.message.chat.id) == False:
        return
    d_gag.add(update, context, redisPool0, c_CHAR)


caps_handler = CommandHandler('gag', gag)
dispatcher.add_handler(caps_handler)

print('初始化完成。')
