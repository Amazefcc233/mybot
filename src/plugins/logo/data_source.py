import io
import base64
import jinja2
import aiohttp
import asyncio
import traceback
from pathlib import Path
from PIL import ImageFont
from bs4 import BeautifulSoup
from PIL import Image, ImageChops

from nonebot.log import logger
from nonebot.adapters.cqhttp import MessageSegment
from src.libs.playwright import get_new_page

dir_path = Path(__file__).parent
template_path = dir_path / 'template'


async def create_logo(texts, style='pornhub'):
    try:
        if style == 'pornhub':
            image = await create_pornhub_logo(texts[0], texts[1])
        elif style == 'youtube':
            image = await create_youtube_logo(texts[0], texts[1])
        elif style == 'douyin':
            image = await create_douyin_logo(' '.join(texts))
        elif style in ['cocacola', 'harrypotter']:
            image = await create_logomaker_logo(' '.join(texts), style)

        if image:
            return MessageSegment.image(f"base64://{base64.b64encode(image).decode()}")
        return None
    except (AttributeError, TypeError, OSError):
        logger.debug(traceback.format_exc())
        return None


async def create_pornhub_logo(left_text, right_text):
    font = ImageFont.truetype('msyh.ttc', 100)
    font_width, _ = font.getsize(left_text + right_text)
    img_width = font_width + 200

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_path.absolute())))
    template = env.get_template('pornhub.html')
    content = template.render(left_text=left_text, right_text=right_text)

    async with get_new_page(viewport={"width": img_width,"height": 250}) as page:
        await page.set_content(content)
        raw_image = await page.screenshot()

    return await trim(raw_image)


def load_woff(name):
    with (template_path / name).open('rb') as f:
        return 'data:application/x-font-woff;charset=utf-8;base64,' + base64.b64encode(f.read()).decode()


def load_png(name):
   with (template_path / name).open('rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()


async def create_youtube_logo(left_text, right_text):
    font = ImageFont.truetype('msyh.ttc', 100)
    font_width, _ = font.getsize(left_text + right_text)
    img_width = font_width + 300

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_path.absolute())))
    env.filters['load_woff'] = load_woff
    env.filters['load_png'] = load_png
    template = env.get_template('youtube.html')
    content = template.render(left_text=left_text, right_text=right_text)

    async with get_new_page(viewport={"width": img_width,"height": 250}) as page:
        await page.set_content(content)
        raw_image = await page.screenshot()

    return await trim(await trim(raw_image))


async def trim(im, format='png'):
    im = Image.open(io.BytesIO(im)).convert('RGB')
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    box = diff.getbbox()
    if box:
        im = im.crop(box)
    output = io.BytesIO()
    im.save(output, format=format)
    return output.getvalue()


async def create_douyin_logo(text):
    async with get_new_page() as page:
        await page.goto('https://tools.miku.ac/douyin_text/')
        try:
            await page.click('button[class="el-button el-button--default el-button--small el-button--primary "]')
            await asyncio.sleep(1)
        except:
            pass
        await page.evaluate('function() {document.querySelector("input[type=checkbox]").click()}')
        await page.click('input[type=text]')
        await page.fill('input[type=text]', text)
        await page.click('button[class="el-button el-button--default"]')
        await asyncio.sleep(2)
        preview = await page.query_selector('div[class="nya-container preview pt"]')
        img = await preview.query_selector('img')
        url = await (await img.get_property('src')).json_value()
        resp = await page.goto(url)
        content = await resp.body()
        return content


async def create_logomaker_logo(text, style='cocacola'):
    url = 'https://logomaker.herokuapp.com/proc.php'
    params = {
        'type': '@' + style,
        'title': text,
        'scale': 200,
        'spaceheight': 0,
        'widthplus': 0,
        'heightplus': 0,
        'fontcolor': '#000000',
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as resp:
            result = await resp.text()
    result = BeautifulSoup(result, 'lxml')
    href = result.find('a', {'id': 'gdownlink'})
    if not href:
        return None

    link = 'https://logomaker.herokuapp.com/' + href['href']
    headers = {
        'Referer': 'https://logomaker.herokuapp.com/gstyle.php'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(link, headers=headers) as resp:
            result = await resp.read()
    return result
