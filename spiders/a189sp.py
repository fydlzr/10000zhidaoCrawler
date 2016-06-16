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

findPhoneID = re.compile('var materialId = \'(.*)\'')
findSXP = re.compile('SXP(\d{14})')
broadbandUrlPrefix = 'http://js.189.cn/nmall/product/broadbandInfo/SXP'
queryPackageXqPrefix = 'http://js.189.cn/nmall/product/queryPackageXq/SXP'
phonePrefix = 'http://js.189.cn/nmall/product/phone/'

def has_tr_no_displayNone(tag):
	return tag.name=='tr' and (tag.has_attr('style')==False or (tag.has_attr('style') and tag['style']!='display:none;'))

def getFirstString(tag):
	for s in tag.stripped_strings:
		return s

def getListSingle(tag):
	l = []
	for s in tag.stripped_strings:
		if s!="":l.append(s)
	return l
def getListString(tag):
	l = ''
	for s in tag.stripped_strings:
		l += s
	return l
def getList(tags):
	l = []

	for tag in tags:
		flag = False
		v = ''
		for s in tag.stripped_strings:
			if s=='':continue
			if flag==False:
				l.append(s)
				flag = True
			else:
				v += s+'  '
		l.append(v)
	return l

def post(url, parameter):
	data = urllib.urlencode(parameter)
	req = urllib2.Request(url, data)
	response = urllib2.urlopen(req)
	return response.read()

class A189spSpider(scrapy.Spider):
	name = "189sp"
	allowed_domains = []
	
	start_urls = (
		# 'http://js.189.cn/nmall/broadband/index',
		# 'http://js.189.cn/flowZone/index.jsp',
		# 'http://js.189.cn/nmall/productList/index?queryType=packageCondition&match4G=4G',
		# 'http://js.189.cn/nmall/productList/index?queryType=mobileCondition&mobile=apple',
		# 'http://js.189.cn/nmall/product/phone/SXP20151109003782.html#dinfo_2',
		'http://www.189.cn/dqmh/tianyiMall/searchMallAction.do?method=shopPhone',
		# 'http://www.189.cn/products/0165417854.html',
	)

	def parse(self, response):
		items = []
		#宽带
		if 'broadband' in response.url:
			bodys = response.body.split('<html>')
			
			for body in bodys:
				soup = bs(body,"lxml")
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
			# values = {'parameter':'FF32=&FF33=',\
			# 'areaCode':'025',\
			# 'sortFlag':'xl',\
			# 'cssFlag':'down',\
			# 'pageindex' : str(pageindex),\
			# 'tableNumber':'03'}
			# sxps = self.get_SXP_LIST('http://js.189.cn/nmall/product/queryPackageList.do', values)
			# for sxp in sxps:
			# 	yield Request(queryPackageXqPrefix+sxp+'.html', callback=self.parse)
			res_items = self.process_TaoCan(1)
			for it in res_items:
				items.append(it)
				yield it
		#终端get_ZhongDuan_SXPList
		elif 'method=shopPhone' in response.url:
			values = {'method':'shopPhone',\
			'xspLeibie':'手机',\
			'pageSize':'555',\
			'internal_search' : '1',\
			'shopId':'10001',\
			'currentPage':1}		

			body = post('http://www.189.cn/dqmh/tianyiMall/searchMallAction.do', values)

			findPhone = re.compile('salesCode":"\d{10}"')
			phones = findPhone.findall(body)
			for p in phones:
				pp = p.split(":")[1].replace("\"","")
				yield Request('http://www.189.cn/products/'+pp+'.html', callback=self.parse)
		elif 'http://www.189.cn/products/' in response.url:
			bodys = response.body.split('<html>')
			
			for body in bodys:
				soup = bs(body ,"lxml")
				item = CrawlerItem()
				titleBox = soup.find('div', class_='titleBox')
				if titleBox == None:
					titleb = soup.find('span', id = 'articleshorttitle')
					if titleb!=None:
						title = titleb.string
					else:
						title = 'None'
				else:
					title = getListString(titleBox)
				item['url'] = response.url
				if title !=None:
					item['title'] = title  

				

				hidden2 = soup.find('div', id='ggcs_con_null')
				if hidden2==None:
					continue
				kv={}
				price = soup.find('span', id='mall_price')
				if price == None:
					kv['price'] = 'None'
				else:
					kv['price'] = price.string.encode('utf-8')
				canshu_s = hidden2.find_all('table')
				if canshu_s==None:
					for s in hidden2.stripped_strings:
						ss = s.split('：')
						kv[ss[0]] = ' '.join(t for t in ss[1:])
				else:
					for canshu in canshu_s:
						if canshu == None:
							for s in hidden2.stripped_strings:
								ss = s.split('：')
								kv[ss[0]] = ' '.join(t for t in ss[1:])
						else:
							tbody = canshu.find('tbody')
							tr_s = tbody.find_all('tr')
							for tr in tr_s:
								td_s = getListSingle(tr)
								if len(td_s)%2==0:
									i = 0
									while i<len(td_s):
										j = i+1
										while j<len(td_s):
											if td_s[j]!="":
												kv[td_s[i]] = td_s[j]
												break
											j+=1
										i = j+1
								else:
									tstr = ''
									for t in td_s[1:]:
										tstr += t
									if tstr!="":
										kv[td_s[0]] = tstr
				item['table2'] = json.dumps(kv,ensure_ascii=False).encode('utf-8')

				item['table'] = ''
				item['need_know'] = ''
				item['faq'] = ''
				items.append(item)
				yield item
				break

		#终端get_ZhongDuan_SXPList
		elif 'queryType=mobileCondition' in response.url:
			values = {'parameter':'FF20=&FF21=&FF22=&FF23=&FF24=&FF25=&FF26=',\
			'sortFlag':'',\
			'cssFlag':'',\
			'pageindex' : '1',\
			'tableNumber':'02'}		

			sxps = self.get_SXP_LIST('http://js.189.cn/nmall/product/queryProductList.do', values)
			for sxp in sxps:
				yield Request(phonePrefix+sxp+'.html#dinfo_2', callback=self.parse)
		#终端ext
		elif 'phone' in response.url:
			phoneId = findPhoneID.search(response.body)
			if phoneId!=None:
				phoneId = phoneId.group(1)
			bodys = response.body.split('<html>')
			
			for body in bodys:
				soup = bs(body,"lxml")
				item = CrawlerItem()
				baby_name_res = soup.find('div', class_='baby_name')
				title = getFirstString(baby_name_res)

				li_s = soup.find('div', class_='baby_info').find_all('li', recursive=False)
				kv = self.getInfoBox(li_s,len(li_s))

				item['url'] = response.url
				if title !=None:
					item['title'] = title
				item['table'] = json.dumps(kv, ensure_ascii=False ).encode('utf-8')
				if phoneId!=None:
					values = {'materialId':phoneId}
					item['table2'] = post('http://js.189.cn/nmall/item/phone/queryMaterialExtendValuePage.json', values)
				item['need_know'] = ''
				item['faq'] = ''
				items.append(item)
				yield item
				break
		elif 'flowZone' in response.url:
			values = {'typeForAD':'100', 'ADType':'100'}
			info = post('http://js.189.cn/flowZone/flowZone_findAdInfoBySourceNew.action', values)
			flow_json = json.loads(info)
			for flow in flow_json['TSR_RESULTARRAY']:
				item = CrawlerItem()
				item['url'] = 'flowZone' + ':' + flow['ADId']
				item['title'] = flow['ADDesc']
				item['table'] = json.dumps(flow, ensure_ascii=False).encode('utf-8')
				item['table2'] = ''
				item['need_know'] = ''
				item['faq'] = ''
				items.append(item)
				yield item


		# sxps = findSXP.findall(response.body)
		# for sxp in sxps:
		# 	yield Request(queryPackageXqPrefix+sxp+'.html', callback=self.parse)

	def getInfoBox(self, tr_s, keyCount):
		tableContent = getList(tr_s)
		kv = {}
		for i in range(0,2*keyCount-1):
			if i%2 == 0:
				kv[tableContent[i]] = tableContent[i+1]
		kv[tableContent[2*keyCount-2]] = ''
		for i in range(2*keyCount-1, len(tableContent)):
			if i < len(tableContent) and 2*keyCount-2<len(tableContent):
				kv[tableContent[2*keyCount-2]] += tableContent[i]
		return kv

	def process(self,item,soup,table_1_res,kd_xqinfo_res,baby_info_res):

		item['title'] = ''
		item['table'] = ''
		item['table2'] = ''
		item['need_know'] = ''
		item['faq'] = ''

		if kd_xqinfo_res!=None:
			item['title'] = kd_xqinfo_res.find('h2').string.strip()
			tr_s = kd_xqinfo_res.find_all(has_tr_no_displayNone)
			kv = self.getInfoBox(tr_s, 4)
			item['table'] = json.dumps(kv, ensure_ascii=False).encode('utf-8')
		

		if table_1_res != None:
			keylist=[]
			valuelist=[]
			trs = table_1_res.find_all('tr', recursive=False)
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
						tds = tr.find_all('td', recursive=False)
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
			li_s = baby_info_res.find_all('li', recursive=False)
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

		pj = json.loads(post('http://js.189.cn/nmall/product/queryPackageList.do', values))
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

	def get_SXP_LIST(self, prefix, values):
		SXPList = []
		pageTotal, res_items = self.get_SinglePage_SXPList(1,prefix,  values)
		SXPList+=(res_items)
		for i in range(2,pageTotal+1):
			values['pageindex'] = str(i)
			pt, res_items = self.get_SinglePage_SXPList(i,prefix,  values)
			SXPList+=(res_items)
		return SXPList
	def get_SinglePage_SXPList(self, pageindex, prefix, values):
		res_items = []
		pj = json.loads(post(prefix, values))
		pageTotal = pj['pageCount']
		for offer in pj['offerList']:
			res_items.append(offer['FNUMBER'])
		return pageTotal, res_items
