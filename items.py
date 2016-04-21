# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # def __init__(self):
    # 	url = ''
    # 	title = ''
    # 	table = ''
    # 	table2 = ''
    # 	need_know = ''
    # 	faq = ''

    url = scrapy.Field()
    title = scrapy.Field()
    table = scrapy.Field()
    table2 = scrapy.Field()
    need_know = scrapy.Field()
    faq = scrapy.Field()
