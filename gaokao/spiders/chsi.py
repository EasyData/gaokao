# -*- coding: utf-8 -*-

import json
import re
import scrapy
from scrapy.http import Request, FormRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose, MapCompose, Join
from scrapy.spiders import CrawlSpider, Rule
from urlparse import urljoin
from w3lib.html import remove_tags
from gaokao.items import *


class ChsiZhuanyeSpider(scrapy.Spider):

    name = "chsi_zhuanye"
    allowed_domains = ["gaokao.chsi.com.cn"]

    def start_requests(self):

        yield Request(url=self.get_url(0, 10))

    def parse(self, response):

        meta = response.meta
        level = meta.get('level', 0)
        categories = meta.get('categories', [])

        if level < 3:
            for e in response.css('li'):
                id = e.css('::attr(id)').extract_first()
                name = e.css('::text').extract_first()
                yield Request(
                    url=self.get_url(level+1, id),
                    meta={
                        'level': level+1,
                        'categories': categories + [{
                            'level': level,
                            'id': id,
                            'name': name,
                        }]
                    }
                )
        else:
            specialities = []
            for e in response.xpath('//tr[td]'):
                specialities.append({
                    'id': e.xpath('td[1]/a/@href').re_first(r'specialityId=(\w+)'),
                    'name': e.xpath('td[1]/a/text()').extract_first(),
                    'code': e.xpath('td[2]/text()').extract_first(),
                })

            yield {
                'categories': categories,
                'specialities': specialities,
            }

    def get_url(self, level, key):

        base_url = 'http://gaokao.chsi.com.cn/zyk/zybk/'

        if level == 0:
            page = 'ccCategory.action'
        elif level == 1:
            page = 'mlCategory.action'
        elif level == 2:
            page = 'xkCategory.action'
        elif level == 3:
            page = 'specialityesByCategory.action'
        else:
            raise Exception('invalid level')

        return '{}{}?key={}'.format(base_url, page, key)


class ChsiDaxueSpider(CrawlSpider):

    name = "chsi_daxue"
    allowed_domains = ["gaokao.chsi.com.cn"]
    start_urls = (
        'http://gaokao.chsi.com.cn/sch/search--ss-on,option-qg,searchType-1.dhtml',
    )
    rules = (
        Rule(LinkExtractor(restrict_xpaths=u'//form[@id="PageForm"]//a[.="下一页"]')),
        Rule(LinkExtractor(restrict_css=u'.search>table:last-of-type td[align]>a'), callback='parse_item'),
    )

    def parse_item(self, response):

        loader = ItemLoader(ChsiDaxueItem(), response)
        loader.add_value('id', response.url, re=ur'schId-(\w+)\.dhtml')
        loader.add_value('url', response.url)
        loader.add_css('logo', u'.r_c_sch_logo>img::attr(src)', MapCompose(lambda url: urljoin('http://gaokao.chsi.com.cn/', url)))
        loader.add_css('name', u'.topImg::text')
        loader.add_css('badges', u'.r_c_sch_attr .r_c_sch_icon::attr(title)')

        data_clean = MapCompose(lambda x: re.sub(r'\s+', ' ', x), unicode.strip)
        loader.add_xpath('type', u'//span[@class="f_bold" and .="院校类型："]/following-sibling::text()', data_clean)
        loader.add_xpath('membership', u'//span[@class="f_bold" and .="院校隶属："]/following-sibling::text()', data_clean)
        loader.add_xpath('province', u'//span[@class="f_bold" and span]/following-sibling::text()', data_clean)
        loader.add_xpath('address', u'//span[@class="f_bold" and .="通讯地址："]/following-sibling::text()', data_clean)
        loader.add_xpath('phone', u'//span[@class="f_bold" and .="联系电话："]/following-sibling::text()', data_clean)
        loader.add_xpath('website', u'//span[@class="f_bold" and .="学校网址："]/following-sibling::a/@href', data_clean)
        loader.add_xpath('backdoor', u'//span[@class="f_bold" and .="特殊招生："]/following-sibling::text()', data_clean)

        def parse_votes():
            xpath = u'//td[@class="tdMydT" and .="{}"]/following-sibling::td/div[@class="rank"]/@rank'
            get_vote = lambda what: float(response.xpath(xpath.format(what)).extract_first() or 0)
            return {
                'overall': get_vote(u'综合满意度'),
                'environment': get_vote(u'校园环境满意度'),
                'life': get_vote(u'生活满意度'),
            }

        loader.add_value('votes', parse_votes())

        def parse_trending():
            css = u'{}>table tr:not(:first-child)'
            def get_trending(what):
                majors = []
                for e in response.css(css.format(what)):
                    majors.append({
                        'id': e.css(u'.tdZytjTDiv>a::attr(href)').re_first(r'specId=(\w+)'),
                        'name': e.css(u'.tdZytjTDiv::attr(title)').extract_first(),
                        'vote': float(e.css(u'.avg_rank::text').extract_first()),
                        'count': int(e.css(u'.c_f00::text, .red::text').extract_first()),
                    })
                return majors
            return {
                'count': get_trending(u'#topNoofPTable'),
                'index': get_trending(u'#topIndexTable'),
                'like': get_trending(u'.r_r_box_zymyd'),
            }

        loader.add_value('trending', parse_trending())

        item = loader.load_item()

        for link in LinkExtractor(restrict_xpaths=u'//h3[contains(., "招生专业")]/span[@class="h3_span_more"]/a').extract_links(response):
            yield Request(link.url, meta={'item': item}, callback=self.parse_zhuanye)

    def parse_zhuanye(self, response):

        item = response.meta['item']
        majors = []

        for outer in response.css(u'#schoolSpeciality>ul.r_zyjs_ul'):
            categories = [
                outer.xpath(u'preceding-sibling::div[@class="r_zyjs_T"][1]/text()').extract_first().strip(),
                outer.css(u'.r_zyjs_type::text').extract_first().strip(),
            ]
            specialities = []
            for inner in outer.css(u'.r_zyjs_majors>.r_zyjs_major_span'):
                specialities.append({
                    'id': inner.css('a::attr(href)').re_first(r'specId=(\w+)'),
                    'name': remove_tags(inner.xpath('.').extract_first()).strip(),
                })
            majors.append({
                'categories': categories,
                'specialities': specialities,
            })

        item['majors'] = majors
        return item
