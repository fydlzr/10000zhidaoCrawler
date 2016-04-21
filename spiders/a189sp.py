# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import scrapy
from bs4 import BeautifulSoup as bs
from scrapy.http import Request
from scrapy.spider import BaseSpider
from crawler.items import CrawlerItem
from selenium import selenium
import re, urllib,urllib2,json

findSXP = re.compile('SXP(\d{14})')
broadbandUrlPrefix = 'http://js.189.cn/nmall/product/broadbandInfo/SXP'
queryPackageXqPrefix = 'http://js.189.cn/nmall/product/queryPackageXq/SXP'

def has_tr_no_displayNone(tag):
	return tag.name=='tr' and (tag.has_attr('style')==False or (tag.has_attr('style') and tag['style']!='display:none;'))

def getFirstString(tag):
	for s in tag.stripped_strings:
		return s

def getList(tag):
	l = []
	for s in tag.stripped_strings:
		l.append(s)
	return l



class A189spSpider(scrapy.Spider):
	name = "189sp"
	allowed_domains = ["js.189.cn"]
	
	start_urls = (
		# 'http://js.189.cn/nmall/broadband/index',
		# 'http://js.189.cn/nmall/product/broadbandInfo/SXP20151225004497.html',
		# 'http://js.189.cn/nmall/productList/index?queryType=packageCondition&match4G=4G',
		'http://js.189.cn/nmall/productList/index?queryType=mobileCondition&mobile=apple',
	)

	# def __init__(self):
	# 	self.verificationErrors = []
 #        self.selenium = selenium("localhost", 4444, "*firefox", "http://www.jb51.net")
 #        self.selenium.start()
 #    def __del__(self):
 #        self.selenium.stop()
 #        print self.verificationErrors

	

	def parse(self, response):
		items = []
		#宽带
		if 'broadband' in response.url:
			bodys = response.body.split('<html>')
			
			for body in bodys:
				soup = bs(body)
				kd_xqinfo_res = soup.find('div', class_='kd_xqinfo')
				baby_info_res = soup.find('div', class_='baby_info')
				table_1_res = soup.find('table', class_='table_1')
				if table_1_res == None:
					table_1_res = soup.find('table', class_='table_1_title')
				if kd_xqinfo_res == None and table_1_res == None and baby_info_res == None:
					continue
				else:
					item = CrawlerItem()
					item['url'] = response.url.strip()
					self.process(item,soup,table_1_res,kd_xqinfo_res, baby_info_res)
					items.append(item)
					yield item
					break

			sxps = findSXP.findall(response.body)
			for sxp in sxps:
				yield Request(broadbandUrlPrefix+sxp+'.html', callback=self.parse)
		#套餐
		elif 'queryType=packageCondition&match4G=4G' in response.url:
			res_items = self.process_TaoCan(1)
			for it in res_items:
				items.append(it)
				yield it
		#终端
		elif 'queryType=mobileCondition' in response.url:
			res_items = self.process_ZhongDuan(1)
			for it in res_items:
				items.append(it)
				yield it

		# sxps = findSXP.findall(response.body)
		# for sxp in sxps:
		# 	yield Request(queryPackageXqPrefix+sxp+'.html', callback=self.parse)

	

	def process(self,item,soup,table_1_res,kd_xqinfo_res,baby_info_res):

		item['title'] = ''
		item['table'] = ''
		item['table2'] = ''
		item['need_know'] = ''
		item['faq'] = ''

		if kd_xqinfo_res!=None:
			item['title'] = kd_xqinfo_res.find('h2').string.strip()
			tr_s = kd_xqinfo_res.find_all(has_tr_no_displayNone)
			tableContent = []
			for tr in tr_s:
				for ss in tr.stripped_strings:
					tableContent.append(ss)
			keyCount = 4
			kv = {}
			for i in range(0,2*keyCount-1):
				if i%2 == 0:
					kv[tableContent[i]] = tableContent[i+1]
			for i in range(2*keyCount-1, len(tableContent)):
					kv[tableContent[2*keyCount-2]] += tableContent[i]
			item['table'] = json.dumps(kv, ensure_ascii=False).encode('utf-8')
		

		if table_1_res != None:
			keylist=[]
			valuelist=[]
			trs = table_1_res.find_all('tr')
			if trs !=None:
				for tr in trs:
					if item['title'] =='':
						if tr.has_attr('class'):
							item['title'] = tr.string.strip()
							continue
						else:
							item['title'] = getFirstString(tr)
							continue
					else:
						tds = tr.find_all('td')
						if len(tds)>3:
							if len(keylist)==0:
								for td in tds:
									if td != None:
										keylist.append(td.string.strip())
							else:
								for td in tds:
									if td != None:
										valuelist.append(td.string.strip())
				if len(keylist) == len(valuelist):
				#if True:
					table1 = {}
					for i in range(len(keylist)):
						table1[keylist[i]]= valuelist[i]
					item['table2'] = json.dumps(table1,ensure_ascii=False).encode('utf-8')

		if baby_info_res != None:
			if item['title']=='':
				baby_name_res = soup.find('div', class_='baby_name')
				item['title'] = item['title'] = getFirstString(tr)
			li_s = baby_info_res.find_all('li')
			kv = {}
			for li in li_s:
				ss = getList(li)

				if len(ss)>1:
					v = '  '.join(s for s in ss[1:])
					kv[ss[0]]=v
			item['table'] = json.dumps(kv, ensure_ascii=False).encode('utf-8')

		need_know_res = soup.find('div', class_='need_know')
		if need_know_res !=None:
			item['need_know'] = str(need_know_res).strip()

		mainer_res = soup.find_all('div', class_='mainer')
		for mainer in mainer_res:
			if item['need_know']=='' and '办理须知' in str(mainer) and mainer.find('div')==None:
				item['need_know'] = str(mainer).strip()
			elif mainer.find('div', class_='qa')!=None:
				item['faq'] = str(mainer).strip()
			# else:

	def process_TaoCan(self, pageindex):
		res_items = []
		values = {'parameter':'FF32=&FF33=',\
			'areaCode':'025',\
			'sortFlag':'xl',\
			'cssFlag':'down',\
			'pageindex' : str(pageindex),\
			'tableNumber':'03'}

		data = urllib.urlencode(values)
		req = urllib2.Request('http://js.189.cn/nmall/product/queryPackageList.do', data)
		response = urllib2.urlopen(req)
		the_page = response.read()
		pj = json.loads(the_page)

		pageTotal = pj['pageCount']

		for offer in pj['offerList']:
			item = CrawlerItem()
			item['url'] = 'http://js.189.cn/nmall/product/queryPackageXq/'+offer['FNUMBER']+'.html'
			item['title'] = offer['FNUMBER']
			item['table'] = json.dumps(offer, ensure_ascii=False ).encode('utf-8')
			item['table2'] = ''
			item['need_know'] = ''
			item['faq'] = ''
			res_items.append(item)

		for i in range(2,pageTotal+1):
			res_items.append(self.process_TaoCan(i))

		return res_items

	def process_ZhongDuan(self, pageindex):
		res_items = []
		values = {'parameter':'FF20=&FF21=&FF22=&FF23=&FF24=&FF25=&FF26=',\
			'sortFlag':'',\
			'cssFlag':'',\
			'pageindex' : str(pageindex),\
			'tableNumber':'02'}		

		data = urllib.urlencode(values)
		req = urllib2.Request('http://js.189.cn/nmall/product/queryProductList.do', data)
		response = urllib2.urlopen(req)
		the_page = response.read()
		pj = json.loads(the_page)

		pageTotal = pj['pageCount']

		for offer in pj['offerList']:
			item = CrawlerItem()
			item['url'] = 'http://js.189.cn/nmall/product/phone/'+offer['FNUMBER']+'.html#dinfo_2'
			item['title'] = offer['FNUMBER']
			item['table'] = json.dumps(offer, ensure_ascii=False ).encode('utf-8')
			item['table2'] = ''
			item['need_know'] = ''
			item['faq'] = ''
			res_items.append(item)

		for i in range(2,pageTotal+1):
			res_items.append(self.process_ZhongDuan(i))

		return res_items
	
