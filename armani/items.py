# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, Compose, MapCompose, TakeFirst


def filter_none(value):
    return '' if value is None else value


def clean_str(value):
    strings = []
    for val in value:
        strings.append(
            val.replace('\r\n', ' ').replace('\t', ' ').replace('  ', '').strip()
        )
    return strings


class ArmaniProductLoader(ItemLoader):
    default_output_processor = TakeFirst()
    name_in = TakeFirst()
    name_out = Compose(filter_none)
    price_in = TakeFirst()
    price_out = Compose(filter_none)
    category_out = Join('')
    # color_out = Compose(filter_none)
    description_in = Compose(filter_none)
    description_out = Compose(clean_str)


class ArmaniItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    category = scrapy.Field()
    sku = scrapy.Field()
    available = scrapy.Field()
    scan_time = scrapy.Field()
    color = scrapy.Field()
    size = scrapy.Field()
    region = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
