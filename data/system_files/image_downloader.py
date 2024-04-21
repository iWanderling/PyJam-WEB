import asyncio
import aiohttp


async def get_file(filename, url, destination, session):
    response = await session.get(url, allow_redirects=True)
    await write_file(filename, destination, response)
    response.close()


async def write_file(filename, destination, response):
    data = await response.read()
    with open(f'static/img/{destination}/{filename}', 'wb') as file:
        file.write(data)


async def download_image_handler(background_to_download, destination):
    tasks = []
    session = aiohttp.ClientSession()
    for background in background_to_download:
        filename, url = background
        task = asyncio.create_task(get_file(filename, url, destination, session))
        tasks.append(task)
    await asyncio.gather(*tasks)
    await session.close()
