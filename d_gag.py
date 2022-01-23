from pickle import FALSE
from telegram import Update
from telegram.ext import CallbackContext
import sys
import redis
import json
# redis 記錄格式： [[剩餘次數,用具名稱],[參與人員陣列]]

def rpoint(redisConnect: redis.Redis, user:str, change:int) -> int:
    """查詢或修改絨度"""
    rediskey: str = 'rpt_' + str(user)
    point = 0
    rpointInfo = redisConnect.get(rediskey)
    if rpointInfo != None and len(rpointInfo) > 0:
        rpointInfo = rpointInfo.decode()
        point = int(rpointInfo)
    if change != 0:
        point += change
        if point < 0:
            point = 0
        redisConnect.set(rediskey,str(point))
    return point


def add(update: Update, context: CallbackContext, redisPool0: redis.ConnectionPool, c_CHAR: list[list[str]]):
    """為他人佩戴口球"""
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
            alert = toUser+' 刚刚挣脱口塞！请给对方 1 分钟的休息时间！'
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
            alert = '抱歉， '+fromUser+' 。你已经为 '+toUser+' 佩戴过口塞了，请在 '+toUser+' 挣脱后再试。'
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


def chk(update: Update, context: CallbackContext, redisPool0: redis.ConnectionPool, c_CHAR: list[list[str]]) -> bool:
    """檢查口球次數是否應該變化"""
    text: str = update.message.text
    fromUser: str = '@'+update.message.from_user.username
    chatID: int = update.message.chat.id
    redisConnect = redis.Redis(connection_pool=redisPool0)
    rediskey: str = 'gag_' + str(chatID) + '_' + str(fromUser)
    gagInfo = redisConnect.get(rediskey)
    if gagInfo != None and len(gagInfo) > 0:
        gagInfo = gagInfo.decode()
        if gagInfo == '0':
            redisConnect.close()
            return False
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
            charAll = c_CHAR[0] + c_CHAR[1]
            for msgChar in text:
                isInChar = False
                for dbChar in (charAll):
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
                rpoint(redisConnect, fromUser, 1)
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
        return True
    redisConnect.close()
    return False
