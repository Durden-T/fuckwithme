import asyncio
import datetime
import json
import random
import sys

from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import DeletePhotosRequest, UploadProfilePhotoRequest
import disk_store
import configparser

random.seed(datetime.datetime.now().timestamp())

logger.remove()
logger.add(sys.stdout)


config = configparser.ConfigParser()
config.read('config.ini')

config = config[config['DEFAULT']['session']]
replys = json.loads(config['replys'])
groups = json.loads(config['groups'])
group_msgs = json.loads(config['group_msgs'])
avatar_paths = json.loads(config.get( 'avatar_paths', fallback='{}'))
name_list = json.loads(config.get( 'name_list', fallback='{}'))
db = disk_store.DiskStorage(file_name=config['session'] + '.db')
api_id = config['api_id']
api_hash = config['api_hash']
admin_ids = json.loads(config['admin_chat_id'])
client = TelegramClient(config['session'], api_id, api_hash)
client.start(phone=config['phone'])

@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    if not event.is_private:
        return
    logger.info(f'received private msg: {event.message.message}')
    if event.chat_id not in admin_ids and db[event.chat_id]:
        logger.info(f'event has been replied: {event.chat_id}')
        return

    db[event.chat_id] = event.stringify()

    await check_time()
    if event.chat_id not in admin_ids:
        await random_delay()
    for msg in random.choice(replys):
        await client.send_message(event.chat_id, msg)
        await asyncio.sleep(5)



async def check_time():
    now = datetime.datetime.now()
    if not (8 <= now.hour < 24):
        next = (now + datetime.timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        sleep_seconds = (next - now).total_seconds()
        await asyncio.sleep(sleep_seconds)


async def random_delay(min=900, max=1800):
    await asyncio.sleep(random.randint(min, max))


async def send_random_message_to_groups():
    if len(groups) == 0 or len(group_msgs) == 0:
        return

    while True:
        await check_time()
        logger.info('start send group')
        now = 0
        for group_id in groups:
            if group_id not in admin_ids:
                now = datetime.datetime.now().timestamp()
                last = db[group_id]
                if last != '':
                    last = float(last)
                else:
                    last = 0
            if group_id in admin_ids or now > last:
                message = random.choice(group_msgs)
                await client.send_message(group_id, message)
                logger.info(f'send {message} to {group_id}')
                db[group_id] = now + random.randint(3*3600,5*3600)
                await random_delay(300, 600)

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
    async for dialog in client.iter_dialogs():
        print(dialog.name, 'has ID', dialog.id)

    if config.getboolean('clean'):
        for dialog in await client.get_dialogs():
            if not dialog.is_channel and not dialog.is_group:
                continue
            if dialog.id not in groups:
                logger.info(f'leave dialog {dialog.name}')
                await client.delete_dialog(dialog)

    await client.run_until_disconnected()





with client:
    client.loop.run_until_complete(asyncio.gather(
        main(),
        send_random_message_to_groups(),
        #periodic_change_profile()
    ))
