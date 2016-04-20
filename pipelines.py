# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class CrawlerPipeline(object):
	def __init__(self):
		self.urls_seen = set()

	def process_item(self, item, spider):


		if item['url'] in self.urls_seen:
			raise DropItem("Duplicate item found: %s" % item)

		
		return item
