# -*- coding: utf-8 -*-

import scrapy
from scrapy.http import Request, FormRequest
from scrapy.linkextractors import LinkExtractor
from gaokao.items import *


class SinaSpider(scrapy.Spider):

    name = 'sina'
    allowed_domains = ['kaoshi.edu.sina.com.cn']

    def start_requests(self):

        #for tab in ['school', 'major', 'batch']:
        for tab in ['major']:
            for year in xrange(2013, 2016):
                for local in xrange(1, 32+1):
                    yield Request(
                        url=self.build_url(tab, year, local),
                        meta={'tab': tab, 'year': year, 'local': local},
                    )

    def parse(self, response):

        meta = response.meta

        callback = getattr(self, 'parse_{}_item'.format(meta['tab']))
        for item in callback(response):
            yield item

        if meta.get('page', 1) == 1:
            cur_page = int(response.css('.pageNumWrap::attr(page)').extract_first())
            max_page = int(response.css('.pageNumWrap::attr(totalpage)').extract_first())
            for page in xrange(2, max_page+1):
                yield Request(
                    url=self.build_url(meta['tab'], meta['year'], meta['local'], page),
                    callback=callback,
                )

    def parse_school_item(self, response):

        for row in response.css('table.tbL2 tr:not(:first-child)'):
            yield SinaSchoolItem(
                tab='school',
                school=row.css('td:nth-child(1)>a::text').extract_first(),
                province=row.css('td:nth-child(2)::text').extract_first(),
                type=row.css('td:nth-child(3)::text').extract_first(),
                batch=row.css('td:nth-child(4)::text').extract_first(),
                year=int(row.css('td:nth-child(5)::text').extract_first()),
                score={
                    'max': int(row.css('td:nth-child(6)::text').extract_first()),
                    'avg': int(row.css('td:nth-child(7)::text').extract_first()),
                }
            )

    def parse_major_item(self, response):

        for row in response.css('table.tbL2 tr:not(:first-child)'):
            yield SinaMajorItem(
                tab='major',
                major=row.css('td:nth-child(1)>a::text').extract_first(),
                school=row.css('td:nth-child(2)>a::text').extract_first(),
                score={
                    'max': int(row.css('td:nth-child(3)::text').extract_first()),
                    'avg': int(row.css('td:nth-child(4)::text').extract_first()),
                },
                province=row.css('td:nth-child(5)::text').extract_first(),
                type=row.css('td:nth-child(6)::text').extract_first(),
                batch=row.css('td:nth-child(7)::text').extract_first(),
                year=int(row.css('td:nth-child(8)::text').extract_first()),
            )

    def parse_batch_item(self, response):

        for row in response.css('table.tbL2 tr:not(:first-child)'):
            yield SinaBatchItem(
                tab='batch',
                year=int(row.css('td:nth-child(1)::text').extract_first()),
                province=row.css('td:nth-child(2)::text').extract_first(),
                type=row.css('td:nth-child(3)::text').extract_first(),
                batch=row.css('td:nth-child(4)::text').extract_first(),
                score=int(row.css('td:nth-child(5)::text').extract_first()),
            )

    def build_url(self, tab, year, local, page=1):

        base_url = 'http://kaoshi.edu.sina.com.cn/college/scorelist?tab={}&syear={}&local={}&page={}'
        tab = '' if tab == 'school' else tab
        return base_url.format(tab, year, local, page)

