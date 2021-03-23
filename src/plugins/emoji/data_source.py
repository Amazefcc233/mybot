import os
import re
import random
import requests
import traceback
from bs4 import BeautifulSoup
from urllib.parse import quote

from nonebot.log import logger

dir_path = os.path.split(os.path.realpath(__file__))[0]


def get_emoji_path(name: str):
    patterns = [(r'(ac\d{2,4})', 'ac'),
                (r'(em\d{2})', 'em'),
                (r'emm(\d{1,3})', 'em_nhd'),
                (r'([acf]:?\d{3})', 'mahjong'),
                (r'(ms\d{2})', 'ms'),
                (r'(tb\d{2})', 'tb'),
                (r'([Cc][Cc]98\d{2})', 'cc98')]

    name = name.strip().split('.')[0].replace(':', '').lower()
    file_ext = ['.jpg', '.png', '.gif']
    for pattern, dir_name in patterns:
        match_obj = re.match(pattern, name)
        if match_obj:
            file_full_name = os.path.join(dir_path, 'images', dir_name, match_obj.group(1))
            for ext in file_ext:
                file_path = file_full_name + ext
                if os.path.exists(file_path):
                    return file_path
    return None


async def get_image(keyword):
    keyword = quote(keyword)
    search_url = 'https://fabiaoqing.com/search/bqb/keyword/{}/type/bq/page/1.html'.format(keyword)
    try:
        search_resp = requests.get(search_url)
        if search_resp.status_code != 200:
            logger.warning('Search failed, url: ' + search_url)
            return ''
        search_result = BeautifulSoup(search_resp.content, 'lxml')
        images = search_result.find_all('div', {'class': 'searchbqppdiv tagbqppdiv'})
        image_num = len(images)
        if image_num <= 0:
            logger.warning('Can not find corresponding image! : ' + keyword)
            return ''
        if image_num >= 3:
            images = images[:3]
        random.shuffle(images)
        return images[0].img['data-original']
    except requests.exceptions.RequestException:
        logger.warning('Error getting image! ' + traceback.format_exc())
        return ''
