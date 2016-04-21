# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json

class CrawlerPipeline(object):
	def __init__(self):
		self.urls_seen = set()
		self.taoCanMiaoShu_seen = set()

	def getOutputStr(self, item):
		outputStr = ''
		keys = ['url','title','table','table2','need_know','faq']
		for k in keys:
			outputStr += k + '\n'
			outputStr += item[k].replace('\n','\t') +'\n'
		return outputStr

	def process_item(self, item, spider):
		if item['url'] in self.urls_seen:
			raise DropItem("Duplicate item found: %s" % item)
		# elif item['table'] 
		else:
			self.urls_seen.add(item['url'])

		if 'broadband' in item['url']:
			
			# if item['table'] != '':
			# 	js = json.loads(item['table'])
			# 	city = js['入网地区：'] +'/'
			# else:
			# 	city = ''
			# filename = 'out/broadbandInfo/' + city + item['url'].split('/')[-1]
			filename = 'out/broadbandInfo/'  + item['url'].split('/')[-1]
			fout = open(filename,'wb')
			fout.write(self.getOutputStr(item))
			fout.close()
		elif 'queryPackageXq' in item['url'] or 'queryType=packageCondition&match4G=4G' in item['url']:
			fout = open('out/queryPackageXq/' + item['title']+'.txt','w')
			fout.write(self.getOutputStr(item))
			fout.close()
		return item
