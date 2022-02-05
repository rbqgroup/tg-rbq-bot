# -*- coding:utf-8 -*-
from encodings import utf_8
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
import hashlib

print('正在初始化...')

c_TGTOKEN = '*:*'
c_REDIS = ['127.0.0.1', 6379, '*']
c_REDISDB = [10, 11]  # 配置庫
c_CHAR: list[list[str]] = [
    ['呜', '哈', '啊', '唔', '嗯', '呃', '哦', '嗷', '呕', '噢', '喔'], ['！', '？', '…', '，']]
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
    text: str = '你好， '+fromUser+' ！\n我只为雅诗指定的群组提供服务。'
    print(text)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()


def echo(update: Update, context: CallbackContext):
    """收到的所有非命令文字訊息"""
    if update == None or update.message == None or update.message.chat == None or update.message.from_user == None or update.message.from_user.is_bot == None or update.message.from_user.is_bot or isPermission(update.message.chat.id) == False:
        return
    text: str = update.message.text
    if len(text) == 0 or text[0] == '/':
        return
    if d_gag.chk(update, context, redisPool0, c_CHAR):
        return
    d_chat.chat(update, context, redisPool1)


def new_member(update, context):
    """新成員加入"""
    if update.message.chat == None or isPermission(update.message.chat.id) == False:
        return
    # print(update.message.from_user.username)
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
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


def about(update: Update, context: CallbackContext):
    """幫助"""
    f = open('help_about.txt', 'r', encoding='utf_8')
    txt = f.read()
    f.close()
    # if hashlib.md5(txt.encode()).hexdigest() != 'dcf0894f267288695a2273924a2c3f57':
    #     txt = '文件保护功能检测到错误，请联系实例维护者。'
    context.bot.send_message(chat_id=update.effective_chat.id, text=txt)


caps_handler = CommandHandler('about', about)
dispatcher.add_handler(caps_handler)


def rbqpoint(update: Update, context: CallbackContext):
    """絨度值查詢"""
    if update == None or update.message == None or update.message.from_user == None or update.message.from_user.username == None:
        return
    user: str = '@'+update.message.from_user.username
    fromUser = user
    if len(context.args) == 1 and len(context.args[0]) > 0 and context.args[0][0] == '@':
        user = context.args[0]
    redisConnect = redis.Redis(connection_pool=redisPool0)
    rediskey: str = 'rpt_' + str(user)
    point = 0
    rpointInfo = redisConnect.get(rediskey)
    redisConnect.close()
    if rpointInfo != None and len(rpointInfo) > 0:
        rpointInfo = rpointInfo.decode()
        point = int(rpointInfo)
    alert = ''
    if fromUser != user:
        alert += fromUser+' 所查询的 '
    alert += user+' 的「绒度」是 '+str(point)+' 。\n该「绒度」值在本 bot 所在的群组中通用。'
    if point == 0:
        if fromUser != user:
            alert += '\n你要帮助 '+user+' 成为绒布球吗？'
        else:
            alert += '\n第一次使用吗？「绒度」会在每「挣扎」（佩戴口塞中并发送符合规则的消息）一次（不是按字符计算），增加 1 。如需帮助，可以输入相关功能帮助命令：例如口塞玩法可以输入 `/gag help` ，了解详细的游玩方法；有关本 bot 相关信息，可以输入 `/about` 了解。'
    elif point <= 10:
        alert += '\n是个可爱的萌新绒布球呢。'
    elif point <= 100:
        alert += '\n是个很有潜力的绒布球呢。'
    elif point <= 500:
        alert += '\n是个合格的绒布球呢。'
    elif point <= 1000:
        alert += '\n是个大号绒布球呢。'
    elif point <= 3000:
        alert += '\n是个巨型绒布球！'
    elif point <= 5000:
        alert += '\n是 个 超 级 绒 布 球 ！'
    elif point <= 10000:
        alert += '\n已 经 是 究 极 绒 布 球 了 ！'
    elif point > 10000:
        alert += '\n本 群 元 老 级 绒 布 球 ！'
    print(alert)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=alert)


caps_handler = CommandHandler('rbqpoint', rbqpoint)
dispatcher.add_handler(caps_handler)

print('初始化完成。')
