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
c_REDISDB = [10, 11]  # 配置庫
c_CHAR: list[list[str]] = [['呜', '嘤', '哈', '啊', '唔', '嗯'], ['！', '？', '…']]
c_CHARALL: list[str] = c_CHAR[0] + c_CHAR[1]

updater = Updater(token=c_TGTOKEN, use_context=True)
dispatcher = updater.dispatcher

# Redis
redisPool0 = redis.ConnectionPool(
    host=c_REDIS[0], port=c_REDIS[1], password=c_REDIS[2], db=c_REDISDB[0])
redisPool1 = redis.ConnectionPool(
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


def chat(update: Update, context: CallbackContext, text: str, fromUser: str):
    """聊天參與"""
    # redisVal: [["txt","<username> 快穿！"],["txt","<username> 心动不如行动！"]]
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


def echo(update: Update, context: CallbackContext):
    """收到的所有非命令文字訊息"""
    if update.message.chat == None or isPermission(update.message.chat.id) == False:
        return
    text: str = update.message.text
    if len(text) == 0 or text[0] == '/':
        return
    fromUser: str = '@'+update.message.from_user.username
    chatID: int = update.message.chat.id
    redisConnect = redis.Redis(connection_pool=redisPool0)
    rediskey: str = 'gag_' + str(chatID) + '_' + str(fromUser)
    gagInfo = redisConnect.get(rediskey)
    if gagInfo != None and len(gagInfo) > 0:
        gagInfo = gagInfo.decode()
        if gagInfo == '0':
            redisConnect.close()
            return
        infoArr = json.loads(gagInfo)
        gagTotal: int = int(infoArr[0])
        gagTotal -= 1
        if gagTotal <= 0:
            redisConnect.set(rediskey, '0', ex=60)
            names: list[str] = []
            first = True
            for name in infoArr:
                if first:
                    first = False
                else:
                    names.append(name)
            alert: str = fromUser + ' 挣脱了被 ' + \
                (' 、 '.join(names))+' 佩戴或加固的口塞球！现在可以自由说话了！（ 1分钟强制休息时间，期间不能再被佩戴口球）'
            print(alert)
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=alert)
        else:
            isOK = True
            for msgChar in text:
                isInChar = False
                for dbChar in c_CHARALL:
                    if msgChar == dbChar:
                        isInChar = True
                        break
                if isInChar == False:
                    isOK = False
                    break
            if isOK:
                infoArr[0] = gagTotal
                gagInfo = json.dumps(infoArr)
                redisConnect.set(rediskey, gagInfo)
                gagTotalStr: str = str(gagTotal)
                print(fromUser+' -1 = '+gagTotalStr)
                singleNum: str = gagTotalStr[-1]
                if singleNum == '5' or singleNum == '0':
                    alert = fromUser+' 加油！还有 '+gagTotalStr+' 次！'
                    print(alert)
                    context.bot.send_message(
                        chat_id=update.effective_chat.id, text=alert)
            else:
                context.bot.delete_message(
                    chat_id=update.message.chat_id, message_id=update.message.message_id)
                print(fromUser+' -0 = '+str(gagTotal))
    redisConnect.close()
    chat(update, context, text, fromUser)


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
    toUser: str = context.args[0]
    if toUser[0] != '@':
        return
    fromUser: str = '@'+update.message.from_user.username
    chatID: int = update.message.chat.id
    redisConnect = redis.Redis(connection_pool=redisPool0)
    rediskey: str = 'gag_' + str(chatID) + '_' + str(toUser)
    gagInfo = redisConnect.get(rediskey)
    alert: str = ''
    if gagInfo != None and len(gagInfo) > 0:
        gagInfo = gagInfo.decode()
        if gagInfo == '0':
            redisConnect.close()
            alert = toUser+' 刚刚挣脱口塞球！请给对方 1 分钟的休息时间！'
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
            redisConnect.set(rediskey, gagInfo)
            alert = fromUser+' 加固了 '+toUser+' 的口塞球！'
        alert += ' '+toUser+' 目前佩戴着被 ' + \
            (' 、 '.join(names))+' 安装或加固的口塞球，还需要挣扎 '+str(gagTotal)+' 次才能把它挣脱！'
    else:
        infoArr = [5, fromUser]
        gagInfo = json.dumps(infoArr)
        redisConnect.set(rediskey, gagInfo)
        alert = fromUser+' 为 '+toUser+' 戴上了口塞球！ '+toUser+' 必须挣扎 5 次才能挣脱它！其他人可以继续用同样指令加固 '+toUser+' 的口塞球（但同一个人只能在对方挣脱后才能再次为对方佩戴或加固口塞球）。 ' + \
            toUser+' 现在只能在消息中发送以下文字「' + \
            ('、'.join(c_CHAR[0]))+'」和中文标点「' + \
            ('、'.join(c_CHAR[1]))+'」，每发送一条消息算作挣扎一次，包含其他字符的消息不能发送！'
    redisConnect.close()
    if fromUser == toUser:
        alert += '居然自己给自己戴口塞球，真是个可爱的绒布球呢！'
    print(alert)
    context.bot.send_message(chat_id=update.effective_chat.id, text=alert)


caps_handler = CommandHandler('gag', gag)
dispatcher.add_handler(caps_handler)

print('初始化完成。')
