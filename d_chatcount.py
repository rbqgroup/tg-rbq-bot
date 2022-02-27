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

