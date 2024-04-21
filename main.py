import asyncio
import datetime
import json
import os
import random

from loguru import logger

import disk_store

from telethon import TelegramClient, events

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
client = TelegramClient(os.getenv('session'), api_id, api_hash)
client.start(phone=os.getenv('phone'))
db = disk_store.DiskStorage(file_name=os.getenv('session')+'.db')
replys = json.loads(os.getenv('replys'))


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    if not event.is_private:
        return
    logger.info(event)
    if db[event.chat_id]:
        logger.info(f'event has been replied: {event.chat_id}')
        return

    now = datetime.datetime.now()
    if not (8 <= now.hour <= 24):
        next = (now + datetime.timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        sleep_seconds = (next - now).total_seconds()
        await asyncio.sleep(sleep_seconds)

    await random_delay()
    await client.send_message(event.chat_id, random.choice(replys))
    #db[event.chat_id] = event.stringify()


async def random_delay(min=0, max=1):
#async def random_delay(min=120, max=600):
    await asyncio.sleep(random.randint(min, max))


with client:
    client.loop.run_until_complete(asyncio.gather(client.run_until_disconnected()))
