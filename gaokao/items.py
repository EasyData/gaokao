# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class GaokaopaiDaxueItem(Item):

    url = Field()
    code = Field()
    name = Field()
    name_en = Field()
    logo = Field()
    image = Field()
    badges = Field()
    intro = Field()
    date = Field()

    affiliation = Field()
    students = Field()
    academicians = Field()
    subjects = Field()
    category = Field()
    doctors = Field()
    masters = Field()

    employment = Field()
    sources = Field()
    genders = Field()
    featured_majors = Field()
    essential_majors = Field()
    fee = Field()

    province = Field()
    city = Field()
    addr = Field()
    phone = Field()
    email = Field()
    home_url = Field()
    enroll_url = Field()
    related = Field()

    majors = Field()


class GaokaopaiZhuanyeItem(Item):

    url = Field()
    code = Field()
    name = Field()

    degree = Field()
    period = Field()
    courses = Field()
    related = Field()

    category = Field()

    detail = Field()
    schools = Field()
    trending = Field()
    employment = Field()
    salary = Field()


class GaokaopaiZhiyeItem(Item):

    url = Field()
    code = Field()
    name = Field()
    category = Field()
    majors = Field()
    detail = Field()


class EolZhiyeItem(Item):

    url = Field()
    code = Field()
    name = Field()
    category = Field()
    category2 = Field()
    detail = Field()


class EolZhuanyeItem(Item):

    url = Field()
    code = Field()
    name = Field()
    ccode = Field()
    cname = Field()
    detail = Field()


class EolDaxueZhuanyeItem(Item):

    school = Field()
    specialty = Field()
    clicks = Field()
    time = Field()

class EolDaxueItem(Item):

    url = Field()
    code = Field()
    code2 = Field()
    name = Field()
    name2 = Field()
    province = Field()
    badges = Field()
    type = Field()
    property = Field()
    level = Field()
    library = Field()
    membership = Field()
    nature = Field()
    fee = Field()
    intro = Field()
    rank = Field()
    rank2 = Field()
    home_url = Field()

    logo = Field()
    enroll_url = Field()
    addr = Field()
    phone = Field()
    email = Field()
    votes = Field()
    image_urls = Field()
    time = Field()


class EolDaxueProvinceFenshuxianItem(Item):

    school = Field()
    province = Field()
    score = Field()
    time = Field()


class EolDaxueZhuanyeFenshuxianItem(Item):

    school = Field()
    specialty = Field()
    score = Field()
    time = Field()

class ChsiDaxueItem(Item):

    id = Field()
    url = Field()
    logo = Field()
    name = Field()
    badges = Field()
    type =Field()
    membership = Field()
    province = Field()
    address = Field()
    phone = Field()
    website = Field()
    backdoor = Field()
    votes = Field()
    trending = Field()
    intro =Field()
    majors = Field()

class SinaSchoolItem(Item):

    tab = Field()
    school = Field()
    province = Field()
    type = Field()
    batch = Field()
    year = Field()
    score = Field()

class SinaMajorItem(Item):

    tab = Field()
    major = Field()
    school = Field()
    score = Field()
    province = Field()
    type = Field()
    batch = Field()
    year = Field()

class SinaBatchItem(Item):

    tab = Field()
    year = Field()
    province = Field()
    type = Field()
    batch = Field()
    score = Field()
