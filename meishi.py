#! /usr/bin/env python
# -*- coding:utf-8 -*-
# Author:Ypp

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pyquery import PyQuery as pq
import re
from TbMeishi.config import *
import pymongo

# browser = webdriver.Chrome()
browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
wait = WebDriverWait(browser, 10)

# 设置窗口大小,默认会比较小
browser.set_window_size(1400,900)

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def search():
    """通过搜索关键字美食返回美食的内容"""
    print("正在搜索")
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        input.send_keys(KEYWORD)
        submit.click()
        # 获取的总页数
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        get_products()
        # 总共多少页,就爬取多少页
        return total.text
    except TimeoutException:
        return search()


def next_page(page_num):
    """爬取下一页内容"""
    print("正在翻页",page_num)
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_num)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_num))
        )
        get_products()
    except TimeoutException:
        next_page(page_num)


def get_products():
    """爬取每一页的宝贝信息"""
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item'))
    )
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        # print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    """保存信息到mongoDB"""
    try:
        if db[MONGO_TABLE].insert(result):
            print("存储到MongoDB成功",result)
    except Exception:
        print("存储到MongoDB失败",result)


def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))
        # print(total)
        # 为了测试方便只爬取10页
        total = 10
        for i in range(2, total + 1):
            next_page(i)
    except Exception:
        print("出错啦！")
    finally:
        browser.close()

if __name__ == '__main__':
    main()
