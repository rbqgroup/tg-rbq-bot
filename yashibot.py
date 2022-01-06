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

print('正在初始化...')

c_TGTOKEN = '*:*'
c_REDIS = ['127.0.0.1', 6379, '*']
c_REDISDB = [10]  # 配置庫

updater = Updater(token=c_TGTOKEN, use_context=True)
dispatcher = updater.dispatcher

# Redis
redis_pool = redis.ConnectionPool(
    host=c_REDIS[0], port=c_REDIS[1], password=c_REDIS[2], db=c_REDISDB[0])


def isPermission(chatID: int) -> bool:
    """檢查該會話是否有許可權使用此機器人"""
    redis_conn = redis.Redis(connection_pool=redis_pool)
    rediskey = 'c_' + str(chatID)
    print('rediskey',rediskey)
    isPass = redis_conn.get(rediskey)
    redis_conn.close()
    print('isPass',isPass)
    if isPass != None and isPass == b'1':
        return True
    print('不能提供服务 ' + str(chatID))
    return False


def start(update: Update, context: CallbackContext):
    """響應 /start"""
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="你好，这里是神楽坂小雅诗。我只为雅诗指定的群组提供服务。")


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()


def echo(update: Update, context: CallbackContext):
    """回顯收到的所有非命令訊息"""
    if isPermission(update.message.chat.id) == False:
        return
    print(update.update_id)
    print(update.message.chat.title)
    print(update.message.chat.id)
    print(update.message.text)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text)


echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)


def caps(update: Update, context: CallbackContext):
    """響應小寫轉大寫命令 caps"""
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)

print('初始化完成。')
