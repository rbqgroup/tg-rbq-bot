from telegram import Update
import redis
import json


def updateUserInfo(redisConnect, from_user):
    """記錄使用者 ID 對應的使用者資訊，以便互動中取得名字以輸出等"""
    userInfo: set[str] = {'is_bot': '0'}
    if from_user.language_code != None and len(from_user.language_code) > 0:
        userInfo['language_code'] = from_user.language_code
    if from_user.last_name != None and len(from_user.last_name) > 0:
        userInfo['last_name'] = from_user.last_name
    if from_user.is_bot != None and from_user.is_bot:
        userInfo['is_bot'] = '1'
    if from_user.first_name != None and len(from_user.first_name) > 0:
        userInfo['first_name'] = from_user.first_name
    if from_user.username != None and len(from_user.username) > 0:
        userInfo['username'] = from_user.username
    userInfoJson = json.dumps(userInfo)
    redisKey: str = 'usr_' + str(from_user.id)
    redisConnect.set(redisKey, userInfoJson, ex=31536000)


def loadUserInfo(redisConnect, userID: int) -> list[str]:
    """獲取記錄的使用者資訊"""
    redisKey: str = 'usr_' + str(userID)
    replyInfo = redisConnect.get(redisKey)
    # {
    #     "is_bot": "0",
    #     "language_code": "zh-hans",
    #     "first_name": "神楽坂雅詩",
    #     "username": "username"
    # }
    if replyInfo != None and len(replyInfo) > 0:
        replyInfo = replyInfo.decode()
        from_user: set[str] = json.loads(replyInfo)
        return from_user
    return None
