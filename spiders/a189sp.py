# -*- coding: utf-8 -*-
import scrapy
import BeautifulSoup as bs


class A189spSpider(scrapy.Spider):
    name = "189sp"
    allowed_domains = ["js.189.cn"]
    start_urls = (
        'http://js.189.cn/nmall/product/broadbandInfo/SXP20151227004507.html',
    )

    def parse(self, response):
    	filename = 'out/' + response.url.split('/')[-1]
        open(filename, 'wb').write(response.body)
        soup = BeautifulSoup(response)        
        
