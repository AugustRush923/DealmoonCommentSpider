import csv
import time
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from lxml import etree


def timer(func):
    def inner(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print('耗时：%s' % (end_time - start_time))
        return result

    return inner


def write2CSV(item):
    with open('dealmoon.csv', 'a+', encoding='utf-8') as csv_file:
        fieldnames = ['postId', 'cId', 'rootId', 'relatedNum', 'userId', 'userName', 'userAvatar', 'isAnonymous',
                      'location', 'clientType', 'reviewTitle', 'reviewContent', 'reviewTime', 'reviewImages']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        # writer.writeheader()
        writer.writerow(item)


@timer
def get_whole_html():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(argument='--headless')
    chrome_options.add_argument(argument='--disable-gpu')
    chrome_options.add_argument(
        'user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.41"')
    chrome_options.add_argument('--no-sandbox')
    # driver = webdriver.Edge(executable_path='msedgedriver')
    driver = webdriver.Chrome(executable_path='chromedriver.exe', options=chrome_options)
    # driver.implicitly_wait(30)
    # 获取网站
    driver.get("https://www.dealmoon.com/en/extra-20-off-vlook-glasses-frame-sale/2014091.html")
    time.sleep(5)

    # 加载整个页面
    js = 'window.scrollTo(0,document.body.scrollHeight)'  # js语句  滚动到底部
    # js = """
    #     let timer = null;
    #     console.log( document.documentElement.scrollTop);
    #     let num = 0;
    #     timer = window.setInterval(function () {
    #         if (num >= document.body.scrollHeight) {
    #             window.clearInterval(timer);
    #             return ;
    #         }
    #         num += 50;
    #         window.scrollTo(0, num);
    #         console.log( document.documentElement.scrollTop);
    #     }, 10)
    # """
    driver.execute_script(js)  # 执行js的方法
    time.sleep(2)
    cmt_more = driver.find_element_by_xpath('//a[@class="dm-cmt-more"]')

    while cmt_more:
        related_more = driver.find_elements_by_xpath(
            '//div[@class="dm-cmt-group all-cmt"]//div[@class="dm-cmt-item"]//a[@class="dm-cmt-related-more"]')
        print(len(related_more))
        for related in related_more:
            related.click()
            time.sleep(2)
        try:
            cmt_more.click()
            time.sleep(2)
        except StaleElementReferenceException:
            break
        time.sleep(2)
        js = """'window.scrollTo(0,document.body.scrollHeight)' """  # js语句  滚动到底部
        # js = """
        #     let times = null;
        #     let nums = document.documentElement.scrollTop;
        #     times = window.setInterval(function () {
        #         if (nums >= document.body.scrollHeight) {
        #             window.clearInterval(times);
        #             return ;
        #         }
        #         nums += 50;
        #         window.scrollTo(0, nums);
        #     }, 70)
        # """
        driver.execute_script(js)  # 执行js的方法
        time.sleep(2)

    dealmoonhtml = driver.page_source

    driver.quit()
    return dealmoonhtml


@timer
def parse(html_page):
    def to_string(value):
        str_value = str(value)
        return str_value.lstrip("['").rstrip("']")

    def to_empty(value):
        return value.lstrip(r"\\n").strip()

    def to_local(value):
        loaction = value.split()
        if "ago" not in loaction:
            del loaction[0]
            return " ".join(loaction)
        return ""

    def to_time(value):
        review_time = value.split()
        if "ago" not in review_time:
            review_time = review_time.pop(0)
            return "".join(review_time)
        return value

    html = etree.HTML(html_page)
    li_list = html.xpath('//div[@class="dm-cmt-group all-cmt"]//div[@class="dm-cmt-item"]')
    print(len(li_list))

    for li in li_list:
        item = {}
        item['postId'] = to_string(li.xpath('./@data-uid'))
        item['cId'] = to_string(li.xpath('./@data-id'))
        item['rootId'] = to_string(li.xpath('./@data-rootid'))
        item['relatedNum'] = to_string(li.xpath('./@data-related-num'))
        item['userId'] = to_string(li.xpath('./div[@class="dm-cmt-avatar"]/a/@href'))
        item['userName'] = to_string(li.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user'))
        item['userAvatar'] = to_string(li.xpath('./div[@class="dm-cmt-avatar"]/a/img/@data-src'))
        item['isAnonymous'] = 'True' if to_string(li.xpath(
            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user')) == "匿名用户" else 'False'
        item['location'] = to_local(to_empty(to_string(li.xpath(
            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()'))))
        item['clientType'] = None
        item['reviewTitle'] = None
        item['reviewContent'] = to_string(li.xpath(
            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-box"]/p[@class="dm-cmt-content"]/span/text()'))
        item['reviewTime'] = to_time(to_empty(to_string(li.xpath(
            './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()'))))
        item['reviewImages'] = to_string(
            li.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-imgs clearfix"]/ul/li/img/@data-src'))
        print(item)
        write2CSV(item)

        if int(to_string(li.xpath('./@data-related-num'))) >= 3:
            for i in range(1, int(to_string(li.xpath('./@data-related-num'))) + 1):
                related_group = li.xpath(
                    './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-related"]/div[@class="dm-cmt-related-group"]/div[@class="dm-cmt-item related"][%d]' % i)

                for related in related_group:
                    related_item = {}
                    related_item['postId'] = to_string(related.xpath('./@data-uid'))
                    related_item['cId'] = to_string(related.xpath('./@data-id'))
                    related_item['rootId'] = to_string(related.xpath('./@data-rootid'))
                    related_item['relatedNum'] = to_string(related.xpath('./@data-related-num'))
                    related_item['userId'] = to_string(related.xpath('./div[@class="dm-cmt-avatar"]/a/@href'))
                    related_item['userName'] = to_string(
                        related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user'))
                    related_item['userAvatar'] = to_string(
                        related.xpath('./div[@class="dm-cmt-avatar"]/a/img/@data-src'))
                    related_item['isAnonymous'] = 'True' if to_string(related.xpath(
                        './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user')) == "匿名用户" else 'False'
                    related_item['location'] = None
                    related_item['clientType'] = None
                    related_item['reviewTitle'] = None
                    related_item['reviewContent'] = to_string(
                        related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-box"]/p/span/text()'))
                    related_item['reviewTime'] = to_empty(to_string(related.xpath(
                        './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()')))
                    related_item['reviewImages'] = None
                    print(related_item)
                    write2CSV(related_item)

        if int(to_string(li.xpath('./@data-related-num'))) > 0 and int(to_string(li.xpath('./@data-related-num'))) < 3:
            for i in range(1, int(to_string(li.xpath('./@data-related-num'))) + 1):
                related_group = li.xpath(
                    './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-related"]/div[@class="dm-cmt-related-group"]/div[@class="dm-cmt-item related default"][%d]' % i)
                for related in related_group:
                    related_item = {}
                    related_item['postId'] = to_string(related.xpath('./@data-uid'))
                    related_item['cId'] = to_string(related.xpath('./@data-id'))
                    related_item['rootId'] = to_string(related.xpath('./@data-rootid'))
                    related_item['relatedNum'] = to_string(related.xpath('./@data-related-num'))
                    related_item['userId'] = to_string(related.xpath('./div[@class="dm-cmt-avatar"]/a/@href'))
                    related_item['userName'] = to_string(
                        related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user'))
                    related_item['userAvatar'] = to_string(
                        related.xpath('./div[@class="dm-cmt-avatar"]/a/img/@data-src'))
                    related_item['isAnonymous'] = 'True' if to_string(related.xpath(
                        './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-submit"]/@data-user')) == "匿名用户" else 'False'

                    related_item['location'] = None
                    related_item['clientType'] = None
                    related_item['reviewTitle'] = None
                    related_item['reviewContent'] = to_string(
                        related.xpath('./div[@class="dm-cmt-txt"]/div[@class="dm-cmt-box"]/p/span/text()'))
                    related_item['reviewTime'] = to_empty(to_string(related.xpath(
                        './div[@class="dm-cmt-txt"]/div[@class="dm-cmt-suffix"]/div[@class="dm-cmt-date"]/text()')))
                    related_item['reviewImages'] = None
                    print(related_item)
                    write2CSV(related_item)


if __name__ == '__main__':
    html_page = get_whole_html()
    parse(html_page)
