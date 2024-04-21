import asyncio
import datetime
import json
import os
import random
import dotenv
from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import DeletePhotosRequest, UploadProfilePhotoRequest

import disk_store

dotenv.load_dotenv()

replys = json.loads(os.getenv('replys'))

groups = json.loads(os.getenv('groups', '{}'))
group_msgs = json.loads(os.getenv('group_msgs', '{}'))

avatar_paths = json.loads(os.getenv('avatar_paths', '{}'))
name_list = json.loads(os.getenv('name_list', '{}'))

db = disk_store.DiskStorage(file_name=os.getenv('session') + '.db')

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
client = TelegramClient(os.getenv('session'), api_id, api_hash)
client.start(phone=os.getenv('phone'))


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    if not event.is_private:
        return
    logger.info(event)
    if db[event.chat_id]:
        logger.info(f'event has been replied: {event.chat_id}')
        return

    await check_time()

    await random_delay()
    for msg in random.choice(replys):
        await client.send_message(event.chat_id, msg)
        await asyncio.sleep(3)

    db[event.chat_id] = event.stringify()


async def check_time():
    now = datetime.datetime.now()
    if not (8 <= now.hour <= 24):
        next = (now + datetime.timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        sleep_seconds = (next - now).total_seconds()
        await asyncio.sleep(sleep_seconds)


async def random_delay(min=0, max=1):
    # async def random_delay(min=120, max=600):
    await asyncio.sleep(random.randint(min, max))


async def send_random_message_to_groups():
    if len(groups) == 0:
        return

    while True:
        await check_time()

        message = random.choice(group_msgs)
        for group_id in groups:
            await random_delay()
            now = datetime.datetime.now().timestamp()
            last = db[group_id]
            if last != '':
                last = float(last)
            else:
                last = 0
            if  now > last:
                await client.send_message(group_id, message)
                logger.info(f'send {message} to {group_id}')
                db[group_id] = now + random.randint(3*3600,5*3600)

        await random_delay(600, 1200)


async def periodic_change_profile():
    if len(avatar_paths) == 0:
        return

    while True:
        # 定时更改头像
        new_avatar_path = random.choice(avatar_paths)
        with open(new_avatar_path, 'rb') as new_avatar:
            await client(DeletePhotosRequest(await client.get_profile_photos('me')))
            await client(UploadProfilePhotoRequest(await client.upload_file(new_avatar)))

        # 定时更改姓名
        new_name = random.choice(name_list)
        await client(UpdateProfileRequest(first_name=new_name))
        # 设定下一次执行时间，比如每周一次
        await asyncio.sleep(7*24*60*60)  # 7*24*60*60


async def main():
    me = await client.get_me()
    logger.info(me.stringify())
    async for dialog in client.iter_dialogs():
        print(dialog.name, 'has ID', dialog.id)
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(asyncio.gather(
        main(),
        send_random_message_to_groups(),
        periodic_change_profile()
    ))
