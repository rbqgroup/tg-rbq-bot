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


def getCount(redisConnect, isDelete: bool) -> set[set[int]]:
    keys1: list[bytes] = redisConnect.keys('can_*')
    allGroup: set[set[int]] = {}
    for key1 in keys1:
        keyStr1: str = key1.decode()  # can_-1001234567890
        keyArr1: list[str] = keyStr1.split('_')
        chatID: int = int(keyArr1[-1])  # -1001234567890
        keys2: list[bytes] = redisConnect.keys('len_'+str(chatID)+'_*')
        nowGroupUsers: set[int] = {}
        for key2 in keys2:
            keyStr2: str = key2.decode()  # len_-1001234567890_123456789
            keyArr2: list[str] = keyStr2.split('_')
            userID: int = int(keyArr2[-1])  # 123456789
            userinfo: set[str] = d_userinfo.loadUserInfo(redisConnect, userID)
            redisKey: str = 'len_'+str(chatID)+'_'+str(userID)  # len_123456789
            if userinfo != None:
                name = ''
                if ('is_bot' in userinfo and userinfo['is_bot'] != "False"):
                    continue
                if ('first_name' in userinfo and len(userinfo['first_name']) > 0):
                    name = userinfo['first_name']
                    if ('last_name' in userinfo and len(userinfo['last_name']) > 0):
                        name += userinfo['last_name']
                if (len(name) == 0 and 'username' in userinfo and len(userinfo['username']) > 0):
                    name = userinfo['username']
                if (len(name) == 0):
                    continue
                if (len(name) == 0 and 'id' in userinfo): # DISABLE
                    name = userinfo['id']
                replyInfo = redisConnect.get(redisKey)  # 16
                if replyInfo != None and len(replyInfo) > 0:
                    userChatCount = int(replyInfo)
                    nowGroupUsers[name] = userChatCount
            if redisConnect.exists(redisKey) > 0:
                if isDelete:
                    redisConnect.delete(redisKey)
        if len(nowGroupUsers) > 0:
            nowGroupUsers = sorted(nowGroupUsers.items(
            ), key=lambda kv: (kv[1], kv[0]), reverse=True)
            allGroup[str(chatID)] = nowGroupUsers
    return allGroup


def sendNewDay(context: CallbackContext, redisConnect):
    onlyView = context == None
    allGroup: set[set[int]] = getCount(redisConnect, not onlyView)
    for groupID in allGroup.keys():
        nowGroupUsers: list = allGroup[groupID]
        groupMeg: str = ''
        redisKey: str = 'can_'+groupID
        replyInfo = redisConnect.get(redisKey)
        groupName: str = ''
        if replyInfo != None and len(replyInfo) > 0:
            replyInfo = replyInfo.decode()
            infoArr: list[str] = replyInfo.split(';')
            if len(infoArr) > 2:
                if infoArr[0] == '0' or len(infoArr[2]) == 0 or infoArr[2] == 'null':
                    continue
                groupMeg = infoArr[2]
                groupName = infoArr[1]
        if len(nowGroupUsers) > 0:
            if not onlyView:
                groupMeg += '\n　\n昨天群里最活跃的人是：'
            i = 1
            for userInfo in nowGroupUsers:
                userName: str = userInfo[0]
                chatCount: int = userInfo[1]
                groupMeg += '\nTOP '+str(i)+' : ' + \
                    userName+' ('+str(chatCount)+')'
                i += 1
                if i > 5:
                    break
        print(groupName + '(' + groupID + ') -> ' + groupMeg)
        if not onlyView:
            context.bot.send_message(chat_id=int(groupID), text=groupMeg)
