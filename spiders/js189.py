# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector
from bs4 import BeautifulSoup as bs
from crawler.items import CrawlerItem

def has_tr_no_displayNone(tag):
	return tag.name=='tr' and (tag.has_attr('style')==False or (tag.has_attr('style') and tag['style']!='display:none;'))


class Js189Spider(CrawlSpider):
    name = "js189"
    allowed_domains = ["189.cn"]
    start_urls = (
        'http://js.189.cn/nmall/broadband/index',
    )
    rules = ( 
      Rule(SgmlLinkExtractor(allow=('broadbandInfo/', )),follow=True, callback='parse_broadbandInfo'),
    )

    def parse_broadbandInfo(self, response):
    	self.log('%s' % response.url)
    	bodys = response.body.split('<html>')
    	items = []
    	filename = 'G:/Github/crawler/out/broadbandInfo/' + response.url.split('/')[-1]
    	fout = open(filename,'wb')
    	for body in bodys:
    		soup = bs(body)
    		kd_xqinfo_res = soup.find('div', class_='kd_xqinfo')
    		if kd_xqinfo_res == None:
    			continue
    		else:
    			item = CrawlerItem()
    			item['url'] = response.url
    			item['title'] = kd_xqinfo_res.find('h2').string
    			fout.write(item['title'] +'\n')
    			tr_s = kd_xqinfo_res.find_all(has_tr_no_displayNone)
    			tableContent = ''
    			for tr in tr_s:
    				for ss in tr.stripped_strings:
    					tableContent += ss + '\n'
    			item['table'] = tableContent
    			item['need_know'] = ''
    			items.append(item)
    			fout.write(item['table'])
    			break
    	
    	fout.close()

    	


    	
