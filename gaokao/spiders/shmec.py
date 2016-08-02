# -*- coding: utf-8 -*-

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from w3lib.html import remove_tags
from gaokao.items import *


class ShmecSpider(CrawlSpider):

    name = 'shmec'
    allowed_domains = ['shmec.gov.cn']
    start_urls = [
        'http://www.shmec.gov.cn/web/jyzt/xkkm2017/index.php',
    ]

    rules = (
        Rule(LinkExtractor(restrict_css=ur'#leftcolumn .tb3')),
        Rule(LinkExtractor(restrict_xpaths=ur'//div[@class="xyy"]//a[@title="下一页"]')),
        Rule(LinkExtractor(restrict_css=ur'#ivs_content ~ .ul02'), callback='parse_item'),
    )

    def parse_item(self, response):

        province = response.css('.dqwz>a:last-child::attr(title)').re_first(ur'2017年(.+?)省?本科')
        school = response.css('.nr>h2::text').extract_first()
        count = len(response.xpath('//div[@id="ivs_content"]/table//tr[1]/td').extract())
        for row in response.xpath('//div[@id="ivs_content"]/table//tr[position()>1]'):
            fields = [remove_tags(i).strip() for i in row.css('td').extract()]
            if count == 4:
                del fields[0]
            if len(fields) == 3:
                rowspan_count = [e.css('::attr(rowspan)').extract_first(1) for e in row.css('td')][-3:]
                rowspan_value = fields
                rowspans = len([i for i in rowspan_count if i > 1])
            elif len(fields) + rowspans == 3:
                new_fields = []
                fields.reverse()
                for k, v in zip(rowspan_count, rowspan_value):
                    if k == 1:
                        new_fields.append(fields.pop())
                    else:
                        new_fields.append(v)
                fields = new_fields
            else:
                continue

            yield ShmecItem(
                province=province,
                school=school,
                major=fields[0],
                require=fields[1],
                remark=fields[2],
            )
