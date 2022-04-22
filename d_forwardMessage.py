
import json
from logging.config import listen
from pyparsing import Forward
from requests import session
import telethon
import asyncio
from telethon import TelegramClient,events
with open('d_forwardMessage.json') as f:
    config = json.load(f)
    api_id = config['api_id']
    api_hash = config['api_hash']
    bot_token = config['bot_token']
    sessionName = config['sessionName']
    listenChannel = config['listenChannel']
    ForwardTo = config['ForwardTo']

# bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
bot = TelegramClient(sessionName, api_id, api_hash).start()


async def send(listenChannel,ForwardTo):
    # -1001501099207
    # await bot.send_message(-1001654047493, 'Start')
    print('Start in {}'.format(ForwardTo))

    @bot.on(events.Album(chats=listenChannel))
    async def albumHandler(event):
        # print(event)
        print('开始执行albumHandler')
        sended = await event.forward_to(ForwardTo)



    # @bot.on(events.NewMessage(chats=-1001621993965))
    # async def messageHandler(event):
    #     # print(event)
    #     sended=await event.forward_to(-1001654047493)
    #     print(sended)
        
    await bot.run_until_disconnected()

asyncio.get_event_loop().run_until_complete(send(listenChannel,ForwardTo))
