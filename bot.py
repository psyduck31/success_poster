import discord, aiohttp, aiofiles, json, asyncio
from time import strftime
from discord.ext import tasks


limit_reached = 4
token = "VK_TOKEN_HERE"
group_id = "183676959"
album_id = "264366559"
group_id_2 = "183705277"
album_id_2 = "263754744"
client = discord.Client()
image_ok = [".jpg", ".jpeg", ".png"]
queue = asyncio.Queue()


@tasks.loop(seconds=0.1)
async def executor():
    task = await queue.get()
    await task
    queue.task_done()


@executor.before_loop
async def before():
    await client.wait_until_ready()


@client.event
async def on_ready():
    print("Ok im good")


async def getUploadServer(token, group_id, album_id):
    url = "https://api.vk.com/method/photos.getUploadServer"
    params = {"album_id": album_id, "group_id": group_id, "v": "5.52", "access_token": token}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return json.loads(await resp.text())['response']['upload_url']


async def uploadAlbum(url, token, group_id):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data={'file1': open("success.jpg", "rb")}) as response:
            response = json.loads(await response.text())
            params = {"server": response['server'], "photos_list": response['photos_list'], "album_id": response['aid'], "hash": response['hash'], "access_token": token, "group_id": response['gid'], "v": "5.52"}
            return params


async def savePhotos(params):
    url = "https://api.vk.com/method/photos.save"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response = json.loads(await response.text())
            return str(response['response'][0]['id'])


async def AddWall(ID, group_id, token, user):
    global limit_reached
    addWallUrl = "https://api.vk.com/method/wall.post"
    AddWallParams = {"owner_id": "-" + group_id, "from_group": "1", "attachments": "photo-" + group_id + "_" + ID, "access_token": token, "message": "by " + user, "v": "5.52"}
    async with aiohttp.ClientSession() as session:
        response = await session.get(addWallUrl, params=AddWallParams)
        response = json.loads(await response.text())
        if 'error' in response:
            if response['error']['error_code'] == 214:
                limit_reached = int(strftime("%d"))


async def save_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open('success.jpg', mode='wb')
                await f.write(await resp.read())
                await f.close()


@client.event
async def on_message(message):
    if message.channel.name.lower() == "success":
        if message.attachments:
            if message.attachments[0].filename[message.attachments[0].filename.rfind('.')::] in image_ok:
                await queue.put(main(message.attachments[0].url, message.author.name))


async def main(pic_url, author):
    global limit_reached
    await save_image(pic_url)
    url = await getUploadServer(token, group_id, album_id)
    params = await uploadAlbum(url, token, group_id)
    photo_id = await savePhotos(params)
    if limit_reached:
        if int(limit_reached) != int(strftime("%d")):
            limit_reached = ''
            await AddWall(photo_id, group_id, token, author)
        else:
            print("Limit reached!")
    else:
        await AddWall(photo_id, group_id, token, author)
    url = await getUploadServer(token, group_id_2, album_id_2)
    params = await uploadAlbum(url, token, group_id_2)
    await savePhotos(params)


if __name__ == '__main__':
    executor.start()
    client.run("BOT_TOKEN_HERE")
