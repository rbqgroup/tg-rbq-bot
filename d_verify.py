# -*- coding:utf-8 -*-
from encodings import utf_8
from pickle import FALSE
from select import select
from telegram import Update
from telegram.ext import CallbackContext
import redis
import random

c_OPPORTUNITIES: int = 2
c_TIMEOUT: int = 120
c_WORDS: list[str] = ['很', '非常', '超', '超级', '想变得']


def welcome(update: Update, context: CallbackContext, redisPool0: redis.ConnectionPool):
    """歡迎新成員"""
    redisConnect = redis.Redis(connection_pool=redisPool0)
    for member in update.message.new_chat_members:
        if (member.is_bot != False):
            continue
        userID: str = str(member.id)
        fromUser: str = userID
        if member.username and len(member.username) > 0:
            fromUser = '@' + member.username
        chatID: str = str(update.message.chat.id)
        redisKey: str = 'vfy0_' + chatID + '_' + userID
        wordRandom: int = random.randint(0, len(c_WORDS)-1)
        word: str = '我'+c_WORDS[wordRandom]+'可爱'
        redisVal: str = str(c_OPPORTUNITIES)+','+word+','+fromUser
        redisConnect.set(redisKey, redisVal, ex=c_TIMEOUT)
        redisKey: str = 'vfy1_' + chatID + '_' + userID
        redisConnect.set(redisKey, redisVal)
        alert: str = ' 你好， '+fromUser+' ！欢迎来到 ' + \
            update.message.chat.title+' ！\n不过，在和大家一起聊天之前，请先完成加群验证。\n请在聊天中发送「/verify ' + \
            word+'」来完成加群验证。\n你有 '+str(c_TIMEOUT) + \
            ' 秒的时间来完成这项验证，如果输入错误或者超时，是坏绒布球，将被移出群组哦。'
        from_user = update.message.from_user
        print(update.effective_chat.id, update.effective_chat.title,
              from_user.id, from_user.username, alert)
        context.bot.send_message(chat_id=update.effective_chat.id, text=alert)
    redisConnect.close()


def chatChk(update: Update, context: CallbackContext, redisPool0: redis.ConnectionPool) -> bool:
    """檢查使用者聊天，是否需要移除"""
    from_user = update.message.from_user
    userID: str = str(from_user.id)
    fromUser: str = userID
    if from_user.username and len(from_user.username) > 0:
        fromUser = '@' + from_user.username
    chatID: str = str(update.message.chat.id)
    redisKey: str = 'vfy1_' + chatID + '_' + userID
    redisConnect = redis.Redis(connection_pool=redisPool0)
    info = redisConnect.get(redisKey)
    redisConnect.close()
    if info != None and len(info) > 0:
        if context.bot.delete_message(
            chat_id=update.message.chat_id, message_id=update.message.message_id):
            print('移除尚未通过验证群员的消息 '+str(update.message.chat_id)+'/'+str(update.message.message_id)+'/'+fromUser+':'+update.message.text)
        else:
            print('移除尚未通过验证群员的消息失败！ '+str(update.message.chat_id)+'/'+str(update.message.message_id)+'/'+fromUser+':'+update.message.text)
        return False
    return True


def timeChk(context: CallbackContext, redisPool0: redis.ConnectionPool):
    """檢查是否驗證超時"""
    redisConnect = redis.Redis(connection_pool=redisPool0)
    keys: list[bytes] = redisConnect.keys('vfy1_*')
    for key1b in keys:
        key1: str = key1b.decode()
        key1Unit: list[str] = key1.split('_')
        groupID: str = key1Unit[1]
        userID: str = key1Unit[2]
        fromUser: str = userID
        info = redisConnect.get(key1)
        if info != None and len(info) > 0:
            info = info.decode()
            infoArr: list[str] = info.split(',')
            fromUser: str = infoArr[2]
        key1Unit.pop(0)
        key1Unit.insert(0, 'vfy0')
        key0: str = '_'.join(key1Unit)
        val0 = redisConnect.get(key0)
        if val0 == None:  # 驗證已經超時，執行封禁
            redisConnect.delete(key1)
            context.bot.ban_chat_member(groupID, userID)
            alert: str = '由于 ' + fromUser + ' 验证输入错误或超时，已被除籍绒布球，我们怀念他。'
            print(groupID, userID, fromUser, alert)
            context.bot.send_message(chat_id=groupID, text=alert)
    redisConnect.close()


def verify(update: Update, context: CallbackContext, redisPool0: redis.ConnectionPool):
    if len(context.args) != 1 or len(context.args[0]) == 0:
        return
    chatID = update.message.chat.id
    userID:str = str(update.message.from_user.id)
    fromUser = userID
    redisKey: str = str(chatID) + '_' + userID
    redisKey0: str = 'vfy0_' + redisKey
    redisKey1: str = 'vfy1_' + redisKey
    redisConnect = redis.Redis(connection_pool=redisPool0)
    info = redisConnect.get(redisKey0)
    if info != None and len(info) > 0:
        info = info.decode()
        infoArr: list[str] = info.split(',')
        remainingTimes: int = int(infoArr[0])
        word: str = infoArr[1]
        fromUser = infoArr[2]
        if context.args[0] == word:
            alert: str = '欢迎， '+fromUser+' ！验证通过！'
            if fromUser[0] != '@':
                alert += '\n你还没有设置用户名，强烈建议前往个人资料中的 username 项，填写一个用户名，以便使用本 bot 提供的各种交互功能。没有 username 时不能使用本 bot 的全部功能。'
            print(update.message.chat.id, update.message.chat.title,
                  update.message.from_user.id, update.message.from_user.username, alert)
            context.bot.send_message(chat_id=chatID, text=alert)
            redisConnect.delete(redisKey0)
            redisConnect.delete(redisKey1)
        else:
            remainingTimes -= 1
            if remainingTimes <= 0:
                redisConnect.delete(redisKey0)
                redisConnect.delete(redisKey1)
                context.bot.ban_chat_member(chatID, userID)
                alert: str = '由于他验证超时，是坏绒布球，我们怀念他。'
                print(update.message.chat.id, update.message.chat.title,
                      update.message.from_user.id, update.message.from_user.username, alert)
                context.bot.send_message(chat_id=chatID, text=alert)
            else:
                redisVal: str = str(remainingTimes) + ',' + word
                redisConnect.set(redisKey0, redisVal, ex=c_TIMEOUT)
                alert: str = '验证输入错误！你还有 '+str(remainingTimes)+' 次机会在限时内重新输入！'
                print(update.message.chat.id, update.message.chat.title,
                      update.message.from_user.id, update.message.from_user.username, alert)
                context.bot.send_message(chat_id=chatID, text=alert)
