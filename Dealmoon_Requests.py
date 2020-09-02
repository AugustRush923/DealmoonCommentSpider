# -*- coding: utf-8 -*-
"""
@author: AugustRush923
@site: http://hdcheung.cn
"""

import csv
import time
import json
from functools import wraps

import requests
from lxml import etree

COUNT = 1

URL = "https://www.dealmoon.com/www/comment/list?lang=en"

HEADERS = {
    'authority': 'www.dealmoon.com',
    'method': 'POST',
    'path': '/www/comment/list?lang=en',
    'scheme': 'https',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-length': '52',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.dealmoon.com',
    'referer': 'https://www.dealmoon.com/en/extra-20-off-vlook-glasses-frame-sale/2014091.html',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.41',
    'x-requested-with': 'XMLHttpRequest',
}

DATA = {
    'resId': 2014091,
    'resType': 'deal',
    'list': 'false',
    'lang': 'en',
    'page': 1
}


def timer(func):
    @wraps(func)
    def inner(*args, **kwargs):
        start_time = time.time()
        res = func(*args, **kwargs)
        end_time = time.time()
        print(end_time-start_time)
        return res
    return inner


class DealmoonSpider:
    def __init__(self, url, headers, data=None, xpath=None):
        self.url = url
        self.headers = headers
        self.data = data
        self.xpath = xpath

    def to_string(self, value):
        str_value = str(value)
        return str_value.lstrip("['").rstrip("']")

    def to_empty(self, value):
        return value.lstrip(r"\\n").strip()

    def to_local(self, value):
        loaction = value.split()
        if "ago" not in loaction:
            del loaction[0]
            return " ".join(loaction)
        return ""

    def to_time(self, value):
        review_time = value.split()
        if "ago" not in review_time:
            review_time = review_time.pop(0)
            return "".join(review_time)
        return value

    def write2CSV(self, item):
        with open('dealmoon.csv', 'a+', encoding='utf-8') as csv_file:
            fieldnames = ['postId', 'cId', 'rootId', 'relatedNum', 'userId', 'userName', 'userAvatar', 'isAnonymous',
                          'location', 'clientType', 'reviewTitle', 'reviewContent', 'reviewTime', 'reviewImages']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            # writer.writeheader()
            writer.writerow(item)

    def get_html_page(self, url, headers, data):
        result = json.loads(requests.post(url=url, headers=headers, data=data).text)
        return result['data']['html']

    def parse_html(self, html_page, xpath):
        html = etree.HTML(html_page)
        comment_list = html.xpath(xpath)
        for comment in comment_list:
                item = {}
                item['postId'] = self.to_string(comment.xpath('./@data-uid'))
                item['cId'] = self.to_string(comment.xpath('./@data-id'))
                item['rootId'] = self.to_string(comment.xpath('./@data-rootid'))
                item['relatedNum'] = self.to_string(comment.xpath('./@data-related-num'))
                item['userId'] = self.to_string(comment.xpath('./div[@class="dm-cmt-avatar"]/a/@href'))
                item['userName'] = self.to_string(
                    comment.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user'))
                item['userAvatar'] = self.to_string(comment.xpath('./div[@class="dm-cmt-avatar"]/a/img/@data-src'))
                item['isAnonymous'] = 'True' if self.to_string(comment.xpath(
                    './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user')) == "匿名用户" else 'False'
                item['location'] = self.to_local(self.to_empty(self.to_string(comment.xpath(
                    './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()'))))
                item['clientType'] = None
                item['reviewTitle'] = None
                item['reviewContent'] = self.to_string(comment.xpath(
                    './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-box"]/p[@class="dm-cmt-content"]/span/text()'))
                item['reviewTime'] = self.to_time(self.to_empty(self.to_string(comment.xpath(
                    './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()'))))
                item['reviewImages'] = self.to_string(
                    comment.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-imgs clearfix"]/ul/li/img/@data-src'))
                print(item)
                self.write2CSV(item)
                if int(self.to_string(comment.xpath('./@data-related-num'))) > 0 and int(
                        self.to_string(comment.xpath('./@data-related-num'))) < 3:
                    for i in range(1, int(self.to_string(comment.xpath('./@data-related-num'))) + 1):
                        related_group = comment.xpath(
                            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-related"]/div[@class="dm-cmt-related-group"]/div[@class="dm-cmt-item related default"][%d]' % i)
                        for related in related_group:
                            related_item = {}
                            related_item['postId'] = self.to_string(related.xpath('./@data-uid'))
                            related_item['cId'] = self.to_string(related.xpath('./@data-id'))
                            related_item['rootId'] = self.to_string(related.xpath('./@data-rootid'))
                            related_item['relatedNum'] = self.to_string(related.xpath('./@data-related-num'))
                            related_item['userId'] = self.to_string(related.xpath('./div[@class="dm-cmt-avatar"]/a/@href'))
                            related_item['userName'] = self.to_string(
                                related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user'))
                            related_item['userAvatar'] = self.to_string(
                                related.xpath('./div[@class="dm-cmt-avatar"]/a/img/@data-src'))
                            related_item['isAnonymous'] = 'True' if self.to_string(related.xpath(
                                './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user')) == "匿名用户" else 'False'

                            related_item['location'] = None
                            related_item['clientType'] = None
                            related_item['reviewTitle'] = None
                            related_item['reviewContent'] = self.to_string(
                                related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-box"]/p/span/text()'))
                            related_item['reviewTime'] = self.to_empty(self.to_string(related.xpath(
                                './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()')))
                            related_item['reviewImages'] = self.to_string(related.xpath(
                                './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-imgs clearfix"]/ul/li/img/@data-src'))
                            print(related_item)
                            self.write2CSV(related_item)
                if int(self.to_string(comment.xpath('./@data-related-num'))) >= 3:
                    self.url = "https://www.dealmoon.com/www/comment/relation?lang=en"
                    self.headers = {
                        'authority': 'www.dealmoon.com',
                        'method': 'POST',
                        'path': '/www/comment/relation?lang=en',
                        'scheme': 'https',
                        'accept': 'application/json, text/javascript, */*; q=0.01',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                        'content-length': '69',
                        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'cookie': 'udid=30DCD01132798A6E8715014C3BF9830A; _pubcid=f66978b0-f9ff-4d18-a602-b543b752fade; _ga=GA1.2.1386000769.1598586031; pbjs-unifiedid=%7B%22TDID%22%3A%22246d9bbf-46b7-4f39-9614-f5e96a2fdb28%22%2C%22TDID_LOOKUP%22%3A%22FALSE%22%2C%22TDID_CREATED_AT%22%3A%222020-08-28T03%3A40%3A25%22%7D; dm-privacy=1; enSiteTip=hide; searchHistoryData=vlook; __gads=ID=ca23755857086671:T=1598586020:S=ALNI_MZ17uL7HKX3vvrjFP-ix0JmfGBAAA; CC=US; x-from-site=US; PHPSESSID=7db847c6d859d1fc8e3b9bed8e14f428; rip_detail=; lastRefreshTime=1598669409; TY_SESSION_ID=62cb156c-3a16-47bb-8054-0685526deb19; _dm_sfa=1; bubbleTopDealNum=6; _gid=GA1.2.1325233121.1598836821; langPcCode=en; lang=en; pbjs-id5id=%7B%22ID5ID%22%3A%22ID5-ZHMOx7yAWgLOgCVq6vkv-MgP1KP5BPoyC2EJsh4Fww%22%2C%22ID5ID_CREATED_AT%22%3A%222020-09-02T02%3A08%3A07.91Z%22%2C%22ID5_CONSENT%22%3Atrue%2C%22CASCADE_NEEDED%22%3Atrue%2C%22ID5ID_LOOKUP%22%3Afalse%2C%223PIDS%22%3A%5B%5D%7D; pbjs-id5id_last=Wed%2C%2002%20Sep%202020%2002%3A08%3A08%20GMT; rip=O; cto_bidid=2s5-pV9mZzlZRThIUmh1djhtUGJsb3JxUE1yZ0paM05YdHB1JTJCTkxSckpNcE5JJTJCMkx1b3ZVVmFpWkglMkJyMzclMkZaS1NYeiUyQkpScGw0a3ExRWR5dHdJWVVhY1F5ZDVvTklHbUR2THhUdUYwanlGV2V0OWclM0Q; cto_bundle=dDr92V9QOEhoUmVzUXAzQ2RWQ0dPVDFZOXV2ckdjMEpLTHhPVnElMkZhdkJ0YlJmOUhnNGxVT2t5SG81TnZCJTJGbEhtTFlRTkRIbmtzRGRhcDVXaXAyb1JoWGN4RGVCQlV5ZEk0U2ZqYTBHMGNHbnFkTW05S3pkNDY0OHpxZ1RKSWFmOUZQeThidzlyb2NOUnRIckZ4b0wyWCUyQjVpTlElM0QlM0Q; _gat=1; cto_bundle=ULe2fV9QOEhoUmVzUXAzQ2RWQ0dPVDFZOXVpeE9jdXlOZXdwbVlmSG9XMWlIYWxia043amFtbFBlYk5hT2c4clE4eVBMVjhubXhlbWZVQVY1V0FzbGxNVVN5cUFiJTJGZ0U3elREWlNEeXZGY2dJVUdSVU11VyUyQnF5cXN5ZHhNNWJBZ0lhV3F3N3dBdVZvRFRWSm0lMkZQMUZnUEQlMkZ5U3lub3FJSUg2bzRIVDZOQ3g3NGNoOCUzRA; cto_bundle=ULe2fV9QOEhoUmVzUXAzQ2RWQ0dPVDFZOXVpeE9jdXlOZXdwbVlmSG9XMWlIYWxia043amFtbFBlYk5hT2c4clE4eVBMVjhubXhlbWZVQVY1V0FzbGxNVVN5cUFiJTJGZ0U3elREWlNEeXZGY2dJVUdSVU11VyUyQnF5cXN5ZHhNNWJBZ0lhV3F3N3dBdVZvRFRWSm0lMkZQMUZnUEQlMkZ5U3lub3FJSUg2bzRIVDZOQ3g3NGNoOCUzRA',
                        'origin': 'https://www.dealmoon.com',
                        'referer': 'https://www.dealmoon.com/en/extra-20-off-vlook-glasses-frame-sale/2014091.html',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'same-origin',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.41',
                        'x-requested-with': 'XMLHttpRequest',
                        'x-tingyun-id': 'TWXvR2MAteU;r=15281372'
                    }
                    self.data = {
                        'commentId': self.to_string(comment.xpath('@data-id')),
                        'resId': '2014091',
                        'resType': 'deal',
                        'isReplyComment': '0',
                        'page': '1'
                    }

                    html = etree.HTML(self.get_html_page(self.url, self.headers, self.data))
                    related_list = html.xpath('//div[@class="dm-cmt-item related"]')
                    for related in related_list:
                        related_item = {}
                        related_item['postId'] = self.to_string(related.xpath('./@data-uid'))
                        related_item['cId'] = self.to_string(related.xpath('./@data-id'))
                        related_item['rootId'] = self.to_string(related.xpath('./@data-rootid'))
                        related_item['relatedNum'] = self.to_string(related.xpath('./@data-related-num'))
                        related_item['userId'] = self.to_string(related.xpath('./div[@class="dm-cmt-avatar"]/a/@href'))
                        related_item['userName'] = self.to_string(
                            related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user'))
                        related_item['userAvatar'] = self.to_string(
                            related.xpath('./div[@class="dm-cmt-avatar"]/a/img/@data-src'))
                        related_item['isAnonymous'] = 'True' if self.to_string(related.xpath(
                            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user')) == "匿名用户" else 'False'
                        related_item['location'] = None
                        related_item['clientType'] = None
                        related_item['reviewTitle'] = None
                        related_item['reviewContent'] = self.to_string(
                            related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-box"]/p/span/text()'))
                        related_item['reviewTime'] = self.to_empty(self.to_string(related.xpath(
                            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()')))
                        related_item['reviewImages'] = self.to_string(related.xpath(
                            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-imgs clearfix"]/ul/li/img/@data-src'))
                        print(related_item)
                        self.write2CSV(related_item)
                    if int(self.to_string(comment.xpath('./@data-related-num'))) >= 10:
                        self.data['page'] = '2'
                        html = etree.HTML(self.get_html_page(self.url, self.headers, self.data))
                        related_list = html.xpath('//div[@class="dm-cmt-item related"]')
                        for related in related_list:
                            related_item = {}
                            related_item['postId'] = self.to_string(related.xpath('./@data-uid'))
                            related_item['cId'] = self.to_string(related.xpath('./@data-id'))
                            related_item['rootId'] = self.to_string(related.xpath('./@data-rootid'))
                            related_item['relatedNum'] = self.to_string(related.xpath('./@data-related-num'))
                            related_item['userId'] = self.to_string(
                                related.xpath('./div[@class="dm-cmt-avatar"]/a/@href'))
                            related_item['userName'] = self.to_string(
                                related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user'))
                            related_item['userAvatar'] = self.to_string(
                                related.xpath('./div[@class="dm-cmt-avatar"]/a/img/@data-src'))
                            related_item['isAnonymous'] = 'True' if self.to_string(related.xpath(
                                './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user')) == "匿名用户" else 'False'
                            related_item['location'] = None
                            related_item['clientType'] = None
                            related_item['reviewTitle'] = None
                            related_item['reviewContent'] = self.to_string(
                                related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-box"]/p/span/text()'))
                            related_item['reviewTime'] = self.to_empty(self.to_string(related.xpath(
                                './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()')))
                            related_item['reviewImages'] = self.to_string(related.xpath(
                                './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-imgs clearfix"]/ul/li/img/@data-src'))
                            print(related_item)
                            self.write2CSV(related_item)

    def runserver(self):
        self.parse_html(self.get_html_page(self.url, self.headers, self.data), self.xpath)


if __name__ == '__main__':
    start_time = time.time()
    while True:
        try:
            DATA['page'] = COUNT
            print(DATA['page'])
            if COUNT == 1:
                xpath = '//div[@class="dm-cmt-group all-cmt"]/div[@class="dm-cmt-list"]/div[@class="dm-cmt-item"]'
                DealmoonSpider(URL, HEADERS, DATA, xpath).runserver()
            xpath = '//div[@class="dm-cmt-item"]'
            DealmoonSpider(URL, HEADERS, DATA, xpath).runserver()
            COUNT += 1
        except AttributeError:
            break
    end_time = time.time()

    print(end_time-start_time)
