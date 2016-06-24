# -*- coding: utf-8 -*-

import json
import re
import scrapy
from scrapy.http import Request, FormRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Compose, MapCompose, Join
from scrapy.spiders import CrawlSpider, Rule
from w3lib.html import remove_tags
from gaokao.items import *


class GaokaopaiDaxueSpider(CrawlSpider):

    name = 'gaokaopai_daxue'
    allowed_domains = ['gaokaopai.com']
    start_urls = ['http://www.gaokaopai.com/daxue.html']

    rules = (
        Rule(LinkExtractor(restrict_xpaths=u'//div[@class="schoolList"]//div[@class="pager"]/a[.="下一页"]')),
        Rule(LinkExtractor(restrict_css=u'.schoolList .tit h3'), callback='parse_item'),
    )

    def parse_item(self, response):
        loader = ItemLoader(item=GaokaopaiDaxueItem(), response=response)

        loader.add_value('url', response.url)
        loader.add_value('code', response.url, re=r'-([^-]+)\.html')

        loader.add_css('name', u'.schoolName>strong::text')
        loader.add_css('name_en', u'.schoolName>.enName::text')
        loader.add_css('logo', u'.schoolLogo>img::attr(src)')
        loader.add_css('image', u'.schoolPic_slide img::attr(src)')
        loader.add_css('badges', u'.schoolName>.st>img::attr(alt)')
        loader.add_css('intro', u'#schoolPage .intro', Join(), Compose(remove_tags, unicode.strip))

        loader.add_xpath('date', u'//div[@id="schoolPage"]//span[.="创建时间"]/following-sibling::div/text()')
        loader.add_xpath('affiliation', u'//div[@id="schoolPage"]//span[.="隶属于"]/following-sibling::div/text()')
        loader.add_xpath('students', u'//div[@id="schoolPage"]//span[.="学生人数"]/following-sibling::div/text()')
        loader.add_xpath('academicians', u'//div[@id="schoolPage"]//span[.="院士人数"]/following-sibling::div/text()')
        loader.add_xpath('subjects', u'//div[@id="schoolPage"]//span[.="重点学科"]/following-sibling::div/text()')
        loader.add_xpath('category', u'//div[@id="schoolPage"]//span[.="学校类型"]/following-sibling::div/text()')
        loader.add_xpath('doctors', u'//div[@id="schoolPage"]//span[.="博士点个数"]/following-sibling::div/text()')
        loader.add_xpath('masters', u'//div[@id="schoolPage"]//span[.="硕士点个数"]/following-sibling::div/text()')

        loader.add_xpath('employment', u'//div[@class="catTitle" and h2[contains(., "就业情况")]]/following-sibling::div[@class="txt"][1]', MapCompose(remove_tags, unicode.strip))
        loader.add_css('sources', u'.studentFrom>script:last-of-type', TakeFirst(), Compose(json.loads, dict), re=r'data: (\[\[.+\]\])')
        loader.add_xpath('genders', u'//div[@class="stuSex"]//div[@class="m" or @class="f"]/div/text()[last()]')

        def parse_featured_majors():
            names = response.css(u'.modContent>.box:first-child>h3::text').extract()
            details = response.css(u'.modContent>.box:first-child>p::text').extract()
            for k, v in zip(names, details):
                yield {
                    'name': k,
                    'intro': v,
                }

        loader.add_value('featured_majors', list(parse_featured_majors()))

        def parse_essential_majors():

            for i in [u"国家品牌", u"国家重点", u"省部重点"]:
                x = u'//h3[.="{}"]/following-sibling::ul[1]/li/a'.format(i)
                for e in response.xpath(x):
                    yield {
                        'url': e.css('::attr(href)').extract_first(),
                        'code': e.css('::attr(href)').re_first(ur'-([^-]+).html'),
                        'name': e.css('::text').extract_first(),
                        'type': i,
                    }

        loader.add_value('essential_majors', list(parse_essential_majors()))

        loader.add_xpath('fee', u'//div[@class="catTitle" and h2[contains(., "学费信息")]]/following-sibling::div[@class="txt"][1]', MapCompose(remove_tags, unicode.strip))

        loader.add_xpath('province', u'substring-before(//div[@id="locationNav"]//a[.="选大学"]/following-sibling::a[1], "的大学")')
        loader.add_xpath('city', u'//div[@class="infos"]//label[.="所处城市："]/following-sibling::text()', MapCompose(unicode.strip))
        loader.add_xpath('addr', u'//div[@class="infos"]//label[.="学校地址："]/following-sibling::text()', MapCompose(unicode.strip))
        loader.add_xpath('phone', u'//div[@class="infos"]//label[.="招生电话："]/following-sibling::text()', MapCompose(unicode.strip))
        loader.add_xpath('email', u'//div[@class="infos"]//label[.="电子邮箱："]/following-sibling::text()', MapCompose(unicode.strip))
        loader.add_css('home_url', u'.website>.a1::attr(href)')
        loader.add_css('enroll_url', u'.website>.a2::attr(href)')
        loader.add_css('related', u'.hotschool li>a:last-child::text')

        item = loader.load_item()

        yield Request(
            url='http://www.gaokaopai.com/daxue-zhuanye-{}.html'.format(item['code'][0]),
            meta={'item': item},
            callback=self.parse_zhuanye
        )

    def parse_zhuanye(self, response):

        item = response.meta['item']
        majors = {}

        for e in response.css(u'.schoolIntro_con2>div'):
            cls = e.css('::attr(class)').extract_first()
            if cls == 'catTitle':
                cat1 = e.css('h2::text').re_first(u'开设(.+)专业')
                majors[cat1] = {}
            elif cls == 'majorCon':
                cat2 = e.css('h3::text').re_first(u'■ (.+)（')
                majors[cat1][cat2] = [remove_tags(i) for i in e.css('ul>li').extract()]
            else:
                pass

        item['majors'] = majors
        yield item


class GaokaopaiZhuanyeSpider(CrawlSpider):

    name = 'gaokaopai_zhuanye'
    allowed_domains = ['gaokaopai.com']
    start_urls = [
        'http://www.gaokaopai.com/zhuanye.html',
        'http://www.gaokaopai.com/zhuanye-0-0-1.html',
    ]

    rules = (
        Rule(LinkExtractor(restrict_css=u'.majorContent .majorDef'), callback='parse_item'),
    )

    def parse_item(self, response):

        loader = ItemLoader(GaokaopaiZhuanyeItem(), response)

        loader.add_value('url', response.url)
        loader.add_css('name', u'.majorTitle>h1::text')

        loader.add_xpath('code', u'//div[@class="majorBase"]/h3[starts-with(., "专业代码：")]/text()', re=ur'：(.+)')
        loader.add_xpath('degree', u'//div[@class="majorBase"]/h3[starts-with(., "授予学位：")]/text()', re=ur'：(.+)')
        loader.add_xpath('period', u'//div[@class="majorBase"]/h3[starts-with(., "修学年限：")]/text()', re=ur'：(.+)')
        loader.add_xpath('courses', u'//div[@class="course"]/h3[.="开设课程："]/following-sibling::p/text()')

        def parse_related():

            for e in response.xpath(u'//div[@class="course"]/h3[.="相近专业："]/following-sibling::a'):
                yield {
                    'url': e.css('::attr(href)').extract_first(),
                    'code': e.css('::attr(href)').re_first(ur'-([^-]+)\.html'),
                    'name': e.css('::text').extract_first(),
                }

        loader.add_value('related', list(parse_related()))

        def parse_category():

            category = []

            for i in [u"学历类别", u"学科门类", u"专业类别"]:
                x = u'//h3[.="{}"]/following-sibling::ul[1]/li[@class="current"]/a'.format(i)
                e = response.xpath(x)
                category.append({
                    'url': e.css('::attr(href)').extract_first(),
                    'code': e.css('::attr(href)').re_first(ur'/zhuanye([-0-9]*)\.html').strip('-'),
                    'name': e.css('::text').extract_first(),
                })

            return category

        loader.add_value('category', parse_category())
        loader.add_css('detail', u'.majorCon')

        item = loader.load_item()

        return Request(
            url='http://www.gaokaopai.com/zhuanye-jiuye-{}.html'.format(item['code'][0]),
            meta={'item': item},
            callback=self.parse_jiuye
        )

    def parse_jiuye(self, response):

        item = response.meta['item']
        loader = ItemLoader(item, response)
        loader.add_css('trending', u'.majorCon>.mTxt', TakeFirst(), Compose(remove_tags, unicode.strip))

        def parse_salary():
            cnt = response.css(u'.salary').re_first(ur'取自([0-9]+)份样本')
            avg = response.css(u'.salary>.money::text').re_first(u'\xa5([0-9]+)')
            txt = response.css(u'.salary>script::text').extract_first()
            if cnt and avg and txt:
                return {
                    'cnt': int(cnt),
                    'avg': int(avg),
                    'xs': json.loads(re.findall(r'categories: (\[.*\])', txt)[0].replace("'", '"')),
                    'ys': json.loads(re.findall(r'data: (\[.*\])', txt)[0]),
                }
            else:
                return None

        loader.add_value('salary', parse_salary())

        def parse_employment():

            obj = {
                'region': [],
                'offer': [],
                'experience': [],
                'degree': [],
            }

            for e in response.css(u'ol.bli>li'):
                obj['region'].append({
                    'city': e.css('.b::text').extract_first(),
                    'jobs': e.css('.c::text').extract_first(),
                })

            for e in response.xpath(u'//h4[.="工资情况"]/following-sibling::ul/li'):
                obj['offer'].append({
                    'salary': e.css('.a::text').extract_first(),
                    'ratio': e.css('.c::text').extract_first(),
                })

            for e in response.xpath(u'//h4[.="经验要求"]/following-sibling::ul/li'):
                obj['experience'].append({
                    'years': e.css('.a::text').extract_first(),
                    'ratio': e.css('.c::text').extract_first(),
                })

            for e in response.xpath(u'//h4[.="学历要求"]/following-sibling::ul/li'):
                obj['degree'].append({
                    'degree': e.css('.a::text').extract_first(),
                    'ratio': e.css('.c::text').extract_first(),
                })

            return obj

        loader.add_value('employment', parse_employment())
        item = loader.load_item()

        return Request(
            url='http://www.gaokaopai.com/zhuanye-paiming-{}.html'.format(item['code'][0]),
            meta={'item': item},
            callback=self.parse_paiming
        )

    def parse_paiming(self, response):

        item = response.meta['item']
        schools = []

        for e in response.css(u'.majorCon a'):
            schools.append({
                'url': e.css('::attr(href)').extract_first(),
                'code': e.css('::attr(href)').re_first(ur'-([0-9]+)\.html'),
                'name': e.css('span::text').extract_first(),
                'rank': e.xpath('./following-sibling::text()').re_first(ur'([0-9A-Z][+-]*)'),
            })

        item['schools'] = schools
        return item


class GaokaopaiZhiye(CrawlSpider):

    name = 'gaokaopai_zhiye'
    allowed_domains = ['gaokaopai.com']
    start_urls = [
        'http://www.gaokaopai.com/zhiye.html',
    ]

    rules = (
        Rule(LinkExtractor(restrict_css=u'.categoryList dd')),
        Rule(LinkExtractor(restrict_xpaths=u'//div[@class="zhiyeContent"]/div[@class="pager"]/a[.="下一页"]')),
        Rule(LinkExtractor(restrict_css=u'.zhiyeList h2'), callback='parse_item'),
    )

    def parse_item(self, response):

        loader = ItemLoader(GaokaopaiZhiyeItem(), response)
        loader.add_value('url', response.url)
        loader.add_value('code', response.url, re=ur'-([^-]+)\.html')
        loader.add_css('name', u'.modTitle>h1::text')

        def parse_category():
            for e in response.css(u'.catType>a'):
                yield {
                    'url': e.css('::attr(href)').extract_first(),
                    'code': e.css('::attr(href)').re_first(ur'-([^-]+)\.html'),
                    'name': e.css('::text').extract_first(),
                }

        loader.add_value('category', list(parse_category()))
        loader.add_css('detail', u'.zhiyeShow')

        item = loader.load_item()

        return FormRequest(
            url='http://www.gaokaopai.com/ajax-career-getRelateMajor.html',
            formdata={'code': item['code'][0]},
            meta={'item': item},
            dont_filter=True,
            callback=self.parse_majors
        )

    def parse_majors(self, response):

        item = response.meta['item']
        data = json.loads(response.body)
        majors = []

        for e in data['data']:
            majors.append({
                'url': 'http://www.gaokaopai.com/zhuanye-jianjie-{}.html'.format(e['major_code']) if e['major_code'] else '',
                'code': e['major_code'],
                'name': e['major_name'],
            })

        item['majors'] = majors
        return item
