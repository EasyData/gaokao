# -*- coding: utf-8 -*-

import json
import math
import scrapy
import time
from scrapy.exceptions import CloseSpider
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose, MapCompose, Join
from string import Template
from urlparse import urljoin
from gaokao.items import *


class EolZhuanyeSpider(scrapy.Spider):

    name = "eol_zhuanye"
    allowed_domains = ["gkcx.eol.cn"]
    start_urls = (
        'http://gkcx.eol.cn/schoolhtm/specialty/10032/list.htm',
    )

    def parse(self, response):

        for outer in response.css('#comapreTable tr:not(:first-child)'):

            if outer.css('td[align="center"]'):
                ccode = outer.css('td[align="center"]>a::attr(id)').extract_first()
                cname = outer.css('td[align="center"]>a::text').extract_first()

            for inner in outer.xpath('td[div[@align="left"]/a]'):
                loader = ItemLoader(item=EolZhuanyeItem(), selector=inner)
                loader.add_value('ccode', ccode)
                loader.add_value('cname', cname)
                loader.add_css('url', 'a::attr(href)', lambda urls: urljoin(self.start_urls[0], urls[0]))
                loader.add_xpath('code', 'following-sibling::td[1]/text()', MapCompose(unicode.strip))
                loader.add_css('name', 'a::text', MapCompose(unicode.strip))
                item = loader.load_item()

                yield Request(url=item['url'][0], meta={'item': item}, callback=self.parse_item)

    def parse_item(self, response):

        item = response.meta['item']
        loader = ItemLoader(item, response)
        loader.add_css('detail', '.query_box')
        yield loader.load_item()


class EolDaxueBaseSpider(scrapy.Spider):

    name = "eol_daxue_base"
    allowed_domains = ["gkcx.eol.cn"]

    base_url = 'http://...&size={}&page={}'
    page_size = 100

    def start_requests(self):

        yield Request(self.get_url(1))

    def parse(self, response):

        data = json.loads(response.body)
        total = int(data['totalRecord']['num'])
        total_page = int(math.ceil(total/float(self.page_size)))

        if total == 0:
            raise CloseSpider('blocked')

        for i in self.parse_item(response):
            yield i

        for page in range(2, total_page+1):
            yield Request(url=self.get_url(page), callback=self.parse_item)

    def parse_item(self, response):

        raise NotImplementedError()

    def get_url(self, page):

        return self.base_url.format(self.page_size, page)


class EolDaxueZhuanyeSpider(EolDaxueBaseSpider):

    name = "eol_daxue_zhuanye"

    base_url = 'http://data.api.gkcx.eol.cn/soudaxue/querySchoolSpecialty.html?messtype=json&size={}&page={}'
    page_size = 100

    def parse_item(self, response):

        data = json.loads(response.body)

        for i in data['school']:

            badges = {
                u'教育部直属': int(i['edudirectly']),
                u'985大学': int(i['f985']),
                u'211大学': int(i['f211']),
            }

            yield EolDaxueZhuanyeItem(
                school={
                    'code': i['schoolid'],
                    'name': i['schoolname'],
                    'province': i['schoolprovince'],
                    'badges': [k for k, v in badges.items() if v]
                },
                specialty={
                    'name': i['specialtyname'] or '',
                    'type': i['specialtytype'] or '',
                    'url': i['specialtyurl'] or '',
                },
                clicks={
                    'total': int(i['clicks']),
                    'month': int(i['monthclicks']),
                    'week': int(i['weekclicks']),
                },
                time=int(time.time())
            )


class EolDaxueSpider(EolDaxueBaseSpider):

    name = "eol_daxue"

    base_url = 'http://data.api.gkcx.eol.cn/soudaxue/queryschool.html?messtype=json&size={}&page={}'
    page_size = 50

    def parse_item(self, response):

        data = json.loads(response.body)

        for i in data['school']:

            badges = {
                u'教育部直属': int(i['edudirectly']),
                u'985大学': int(i['f985']),
                u'211大学': int(i['f211']),
                u'自主招生试点': int(i['autonomyrs']),
            }

            yield EolDaxueItem(
                code=i['schoolid'],
                code2=i['schoolcode'] or '',
                name=i['schoolname'],
                name2=i['oldname'] or '',
                province=i['province'] or '',
                badges=[k for k, v in badges.items() if v],
                type=i['schooltype'] or '',
                property=i['schoolproperty'] or '',
                level=i['level'] or '',
                library=i['library'] or '',
                membership=i['membership'] or '',
                nature=i['schoolnature'] or '',
                fee=i['shoufei'] or '',
                intro=i['jianjie'] or '',
                rank=int(i['ranking']),
                rank2=int(i['rankingCollegetype']),
                home_url=i['guanwang'] or '',
                time=int(time.time()),
            )


class EolDaxueProvinceFenshuxianSpider(EolDaxueBaseSpider):

    name = "eol_daxue_province_fenshuxian"

    base_url = 'http://data.api.gkcx.eol.cn/soudaxue/queryProvinceScore.html?messtype=json&fsyear=$year&size={}&page={}'
    page_size = 50

    def __init__(self, year='2015', *args, **kwargs):
        super(EolDaxueProvinceFenshuxianSpider, self).__init__(*args, **kwargs)
        self.base_url = Template(self.base_url).safe_substitute({
            'year': year
        })

    def parse_item(self, response):

        data = json.loads(response.body)

        for i in data['school']:
            yield EolDaxueProvinceFenshuxianItem(
                school={
                    'code': i['schoolid'],
                    'name': i['schoolname'],
                },
                province={
                    'name': i['localprovince'],
                    'score': int(0 if i['provincescore'] in ['--', []] else i['provincescore']),
                },
                score={
                    'year': int(i['year']),
                    'type': i['studenttype'] or '',
                    'batch': i['batch'] or '',
                    'avg': int(0 if i['var'] in ['--', []] else i['var']),
                    'max': int(0 if i['max'] in ['--', []] else i['max']),
                    'min': int(0 if i['min'] in ['--', []] else i['min']),
                    'delta': int(0 if i['fencha'] in ['--', []] else i['fencha']),
                    'url': i['url'] or '',
                },
                time=int(time.time())
            )


class EolDaxueZhuanyeFenshuxianSpider(EolDaxueBaseSpider):

    name = "eol_daxue_zhuanye_fenshuxian"

    base_url = 'http://data.api.gkcx.eol.cn/soudaxue/querySpecialtyScore.html?messtype=json&fsyear=$year&size={}&page={}'
    page_size = 50

    def __init__(self, year='2015', *args, **kwargs):
        super(EolDaxueZhuanyeFenshuxianSpider, self).__init__(*args, **kwargs)
        self.base_url = Template(self.base_url).safe_substitute({
            'year': year
        })

    def parse_item(self, response):

        data = json.loads(response.body)

        for i in data['school']:
            yield EolDaxueZhuanyeFenshuxianItem(
                school={
                    'code': i['schoolid'],
                    'name': i['schoolname'],
                },
                specialty={
                    'name': i['specialtyname'] or '',
                },
                score={
                    'year': int(i['year']),
                    'province': i['localprovince'] or '',
                    'type': i['studenttype'] or '',
                    'batch': i['batch'] or '',
                    'avg': int(0 if i['var'] in ['--', []] else i['var']),
                    'max': int(0 if i['max'] in ['--', []] else i['max']),
                    'min': int(0 if i['min'] in ['--', []] else i['min']),
                    'url': i['url'] or '',
                },
                time=int(time.time())
            )
