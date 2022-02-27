from d_gag import add
from telegram import Update
from telegram.ext import CallbackContext
import redis
import json
import d_userinfo


def updateCount(update: Update, redisPool0: redis.ConnectionPool):
    """聊天积分写入"""
    chatID: str = str(update.message.chat.id)
    fromUserID: str = str(update.message.from_user.id)
    # redisVal:
    redisConnect = redis.Redis(connection_pool=redisPool0)
    d_userinfo.updateUserInfo(redisConnect, update.message.from_user)
    redisKey: str = 'len_' + fromUserID
    redisConnect.incr(redisKey, amount=1)
    redisKey: str = 'len_' + chatID + '_' + fromUserID
    redisConnect.incr(redisKey, amount=1)
    redisConnect.close()


def getCount(redisConnect) -> set[set[int]]:
    keys1: list[bytes] = redisConnect.keys('can_*')
    allGroup: set[set[int]] = {}
    for key1 in keys1:
        keyStr1: str = key1.decode()
        keyArr1: list[str] = keyStr1.split('_')
        chatID: int = int(keyArr1[-1])
        keys2: list[bytes] = redisConnect.keys('len_'+str(chatID)+'_*')
        nowGroupUsers: set[int] = {}
        for key2 in keys2:
            keyStr2: str = key2.decode()
            keyArr2: list[str] = keyStr2.split('_')
            userID: int = int(keyArr2[-1])
            userinfo: set[str] = d_userinfo.loadUserInfo(redisConnect, userID)
            redisKey: str = 'len_'+str(chatID)+'_'+str(userID)
            if userinfo != None and 'username' in userinfo:
                replyInfo = redisConnect.get(redisKey)
                if replyInfo != None and len(replyInfo) > 0:
                    userChatCount = int(replyInfo)
                    nowGroupUsers[userinfo['username']] = userChatCount
            if redisConnect.exists(redisKey) > 0:
                redisConnect.delete(redisKey)
        if len(nowGroupUsers) > 0:
            nowGroupUsers = sorted(nowGroupUsers.items(
            ), key=lambda kv: (kv[1], kv[0]), reverse=True)
            allGroup[str(chatID)] = nowGroupUsers
    return allGroup


def sendNewDay(context: CallbackContext, redisConnect):
    allGroup: set[set[int]] = getCount(redisConnect)
    for groupID in allGroup.keys():
        nowGroupUsers: list = allGroup[groupID]
        groupMeg: str = ''
        redisKey: str = 'can_'+groupID
        replyInfo = redisConnect.get(redisKey)
        if replyInfo != None and len(replyInfo) > 0:
            replyInfo = replyInfo.decode()
            infoArr: list[str] = replyInfo.split(';')
            if len(infoArr) > 2:
                if infoArr[0] == '0' or len(infoArr[2]) == 0 or infoArr[2] == 'null':
                    continue
                groupMeg = infoArr[2]
        if len(nowGroupUsers) > 0:
            groupMeg += '\n　\n昨天群里最活跃的人是：'
            i = 1
            for userInfo in nowGroupUsers:
                userName: str = userInfo[0]
                chatCount: int = userInfo[1]
                groupMeg += '\nTOP '+str(i)+' : @' + \
                    userName+' ('+str(chatCount)+')'
                i += 1
                if i > 5:
                    break
        print(groupID + ' -> ' + groupMeg)
        context.bot.send_message(chat_id=int(groupID), text=groupMeg)
