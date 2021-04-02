import os
from nonebot import export, on_regex, on_endswith, on_shell_command
from nonebot.rule import ArgumentParser
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, Event, MessageSegment

from nonebot.log import logger

from .data_source import get_emoji_path, get_image, make_emoji, emojis

export = export()
export.description = '表情包'
export.usage = 'Usage:\n  1、98表情包，包含"cc98xx"、"acxx"、"tbxx"、"emxx"、"msxx"、"a/c/f:xxx"\n' \
    '  2、{keyword}.jpg，将会回复相关的表情包\n' \
    '  3、emoji -t {type} {text}，表情包制作，发送 "emoji list" 查看支持的表情包列表'
export.notice = 'Notice:\n  由于NHD表情"emxx"与98冲突，用"emmxx"代替'
export.help = export.description + '\n' + export.usage + '\n' + export.notice

ac = on_regex(r'^ac\d{2,4}$', priority=19)
em = on_regex(r'^em\d{2}$', priority=19)
em_nhd = on_regex(r'^emm\d{1,3}$', priority=19)
mahjong = on_regex(r'^[acf]:?\d{3}$', priority=19)
ms = on_regex(r'^ms\d{2}$', priority=19)
tb = on_regex(r'^tb\d{2}$', priority=19)
cc98 = on_regex(r'^[Cc][Cc]98\d{2}$', priority=19)

get_jpg = on_endswith('.jpg', priority=23)


@ac.handle()
@em.handle()
@em_nhd.handle()
@mahjong.handle()
@ms.handle()
@tb.handle()
@cc98.handle()
async def _(bot: Bot, event: Event, state: T_State):
    file_name = str(event.get_message()).strip()
    file_path = get_emoji_path(file_name)
    if file_path:
        await bot.send(event=event, message=MessageSegment.image(file='file://' + file_path))
    else:
        await bot.send(event=event, message="找不到该表情")


@get_jpg.handle()
async def _(bot: Bot, event: Event, state: T_State):
    keyword = str(event.get_message()).strip()
    keyword = os.path.splitext(keyword)[0]
    img_url = await get_image(keyword)
    if not img_url:
        await get_jpg.finish(message="找不到相关的图片")
    await get_jpg.send(message=MessageSegment.image(file=img_url))
    await get_jpg.finish()


emoji_parser = ArgumentParser()
emoji_parser.add_argument('-t', '--type', type=str)
emoji_parser.add_argument('text', nargs='+')

emoji = on_shell_command('emoji', aliases={'表情包'}, parser=emoji_parser, priority=28)


@emoji.handle()
async def _(bot: Bot, event: Event, state: T_State):
    help_msg = 'Usage:\n  emoji -t {type} {text}，发送 "emoji list" 查看支持的表情包列表'

    args = state['args']
    if not hasattr(args, 'text'):
        await emoji.finish(help_msg)

    if args.text[0] == 'list':
        message = '支持的表情包：'
        for i, e in enumerate(emojis):
            message += f"\n{i}. {'/'.join(e['names'])}，需要 {e['input_num']} 个输入"
        await emoji.finish(message)

    if not args.type:
        await emoji.finish(help_msg)

    type = str(args.type)
    num = -1
    if type.isdigit() and 0 <= int(type) < len(emojis):
        num = int(type)
    else:
        for i, e in enumerate(emojis):
            if type in e['names']:
                num = i
    if num == -1:
        await emoji.finish('暂不支持制作该表情包，发送 "emoji list" 查看支持的列表')

    texts = args.text
    if len(texts) != emojis[num]['input_num']:
        await emoji.finish(f"该表情包需要 {emojis[num]['input_num']} 个输入")

    await emoji.send(message='请稍候...')
    msg = await make_emoji(num, texts)
    await emoji.send(message=msg)
    await emoji.finish()
