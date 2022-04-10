from re import A
import time
import datetime
from telegram import Update
from telegram.ext import CallbackContext
import os
import platform
import ctypes
import psutil
import redis


def ping(update: Update, context: CallbackContext, starttime: datetime, permission: bool, redisPool0: redis.ConnectionPool, redisPool1: redis.ConnectionPool):
    grouptitle: str = '私人'
    if update.message.chat.title != None:
        grouptitle = update.message.chat.title
    elif update.message.from_user.username != None:
        grouptitle = update.message.from_user.username
    groupinfo: str = grouptitle + '」'
    chatID: int = update.message.chat.id
    if update.message.chat == None or permission == False:
        groupinfo += '没有'
    else:
        groupinfo += '具有'
    t = int(time.time())
    endtime = datetime.datetime.now()
    runsec: int = (endtime - starttime).seconds
    redisConnect0 = redis.Redis(connection_pool=redisPool0)
    redisConnect1 = redis.Redis(connection_pool=redisPool1)
    alerts: list[str] = [
        'pong',
        '雅诗电子绒布球 v2.0.1',
        '服务器时间戳: '+str(t)+' 秒。',
        '距离上次重新启动: '+str(runsec)+' 秒。',
        '可用磁盘: '+getLocalSpace('/')+' MB',
        '可用内存: '+getMem()+' MB',
        'CPU使用: '+getCpu()+' %',
        '数据库使用: 0: '+str(redisConnect0.dbsize())+' 1: '+str(redisConnect1.dbsize()),
        '当前会话「'+groupinfo+'使用许可权。',
        '有关更多信息请参阅 `/about` 。',
        '　　　　　本 BOT 具有超级绒力。'
    ]
    redisConnect0.close()
    redisConnect1.close()
    alert = '\n'.join(alerts)
    print(update.message.chat.id, update.message.chat.title,
          update.message.from_user.id, update.message.from_user.username, alert)
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=alert)


def getLocalSpace(folder):
    folderTemp = folder
    if not os.path.exists(folderTemp):
        folderTemp = os.getcwd()
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(
            folderTemp), None, None, ctypes.pointer(free_bytes))
        return "%0.2f" % (free_bytes.value / 1024 / 1024)
    else:
        st = os.statvfs(folderTemp)
        return "%0.2f" % (st.f_bavail * st.f_frsize / 1024 / 1024)


def getMem() -> str:
    data = psutil.virtual_memory()
    total = data.total  # 总内存,单位为byte
    free = data.available  # 可用内存
    return "%0.2f" % (free / 1024 / 1024)


def getCpu() -> str:
    cpu = "%0.2f" % psutil.cpu_percent(interval=1)
    return cpu


alerts: list[str] = [
    '服务器时间戳: '+str(time.time())+' 秒。',
    '可用磁盘: '+getLocalSpace('/')+' MB',
    '可用内存: '+getMem()+' MB',
    'CPU使用: '+getCpu()+' %',
]
text = '\n'.join(alerts)
print(text)
