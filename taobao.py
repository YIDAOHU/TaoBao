# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from lxml import etree
import pymongo
from bson.objectid import ObjectId


driver = webdriver.PhantomJS()
# 设置等待
wait = WebDriverWait(driver, 10)

# mongodb配置
MONGO_URL = '127.0.0.1'
MONGO_DB = 'taobao'
MONGO_TABLE = 'product'
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def search():
    """
    进行搜索
    """
    try:
        driver.get('https://www.taobao.com/')
        # 等待搜索框出现
        input_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#q')))
        # 等待搜索按钮出现
        submit = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))
        # 输入搜索关键字
        input_button.send_keys(u'辣条')
        # 点击进行搜索
        submit.click()
        # 等待总页数加载出来
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    """
    进行翻页
    """
    try:
        print u'正在翻页：%d' % page_number
        # 等待页面输入框出现
        input_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > input')))
        # 等待确定按钮出现
        submit = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        # 清空页码框
        input_button.clear()
        # 输入页码
        input_button.send_keys(page_number)
        # 点击确定
        submit.click()
        # 确定页面选定(高亮元素）
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    """
    解析商品信息
    """
    # 等待商品信息加载完成
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = driver.page_source
    text = etree.HTML(html)
    info = {}
    items = text.xpath('//div[@id="mainsrp-itemlist"]//div[@class="items"]')
    for item in items:
        info["image"] = item.xpath('//div[@class="pic"]/a/img/@src')[0]
        info["price"] = item.xpath('//div[contains(@class,"item")]/div[2]/div[1]/div[1]/strong/text()')[0]
        info["deal"] = item.xpath('//div[@class="deal-cnt"]/text()')[0]
        info["title"] = item.xpath('//div[@class="pic"]/a/img/@alt')[0]
        info["shop"] = item.xpath('//div[@class="shop"]/a/span[2]/text()')[0]
        info["location"] = item.xpath('//div[@class="location"]/text()')[0]
        # 设置id
        info["_id"] = ObjectId()
        save_to_mongo(info)
        

def save_to_mongo(result):
    """
    保存到mongodb
    """
    db[MONGO_TABLE].insert(result)


def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, total+1):
        next_page(i)


if __name__ == '__main__':
    main()