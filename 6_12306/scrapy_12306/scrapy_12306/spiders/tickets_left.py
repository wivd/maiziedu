# -*- coding: utf-8 -*-
import time
import datetime
import json
import urllib

import pymysql.cursors

import scrapy
from scrapy.http.request import Request
from scrapy_12306.items import BriefDeltaItem
from scrapy_12306.items import StationCodeItem
from scrapy_12306.items import TicketItem
from scrapy_12306.items import CommitItem

class TicketsSpider(scrapy.Spider):
    name = 'TicketsSpider'
    start_urls = ['https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.8936']

    custom_settings = {
            'ITEM_PIPELINES': {
                'project28.pipelines.Tikcets_left_SQLPipeline': 300,
            },
    }
    # 定义一个静态方法，可以直接通过类名来调用
    # 这正是27.数据量分析中的那个方法
    # 获取所有可到达的路线
    @staticmethod
    def fetch_routes():
        conn = pymysql.connect(host = 'localhost',
                                    port = 3306,
                                    user = '12306',
                                    passwd = '12306',
                                    db = '12306-train',
                                    charset = 'utf8')


        select = "select * from train_infos"

        schedules = {}
        with conn.cursor() as cursor:
            cursor.execute(select)
            count = 0
            for results in cursor.fetchall():
                if results[0] not in schedules:
                    schedules[results[0]] = {results[1]:results[2]}
                else:
                    schedules[results[0]][results[1]] = results[2]


        routes = {}
        for key in schedules:
            route = schedules[key]

            seq = sorted(route)
            len1 = len(seq)
            for i in range(0, len1):
                if route[seq[i]] not in routes:
                    tmp = set()
                    routes[route[seq[i]]] = tmp
                else:
                    tmp = routes[route[seq[i]]]
                for j in range(i + 1, len1):
                    tmp.add(route[seq[j]])
        return routes


    def parse(self, response):
        station_str = response.body.decode("utf-8")
        stations = station_str.split(u"@")
        results = {}

        for i in range(1, len(stations)):
            station = stations[i].split(u"|")
            results[station[1]] = station[2]
            item = StationCodeItem()
            item["name"] = station[1]
            item["code"] = station[2]
            yield item

        yield CommitItem()
        # 通过类名调用这个静态方法获取所有路线
        routes = TicketsSpider.fetch_routes()

        url = "https://kyfw.12306.cn/otn/lcxxcx/query?purpose_codes=ADULT&"
        t = (datetime.datetime.now() + datetime.timedelta(days = 3)).strftime("%Y-%m-%d")
        for s in routes:
            if s in results:
                code_s = results[s]
            else:
                self.logger.warning("code miss " + s)
                continue
            for e in routes[s]:
                if e in results:
                    code_e = results[e]
                else:
                    self.logger.warning("code miss " + e)
                    continue
                 
            params = u"queryDate=" + t + u"&from_station=" + code_s + u"&to_station=" + code_e

            yield Request(url + params, callback = self.parse_ticket, meta = {"s":s, "e":e}) 

    def parse_ticket(self, response):
        datas = json.loads(response.body)

        if "datas" not in datas["data"]:
            self.logger.info("there is no data " + response.meta["s"] + " " + response.meta["e"])
            return

        for data in datas["data"]["datas"]:
            deltaItem = BriefDeltaItem()

            deltaItem["code"] = data["station_train_code"]
            deltaItem["seat_type"] = data["seat_types"]
            yield deltaItem

            item = TicketItem()
            item["train_no"] = data["train_no"]
            item["start"] = data["from_station_name"]
            item["end"] = data["to_station_name"]
            item["swz"] = data["swz_num"]
            if item["swz"] == '--':
                item["swz"] = -1
            item["tz"] = data["tz_num"]
            if item["tz"] == '--':
                item["tz"] = -1
            item["zy"] = data["zy_num"]
            if item["zy"] == '--':
                item["zy"] = -1
            item["ze"] = data["ze_num"]
            if item["ze"] == '--':
                item["ze"] = -1
            item["gr"] = data["gr_num"]
            if item["gr"] == '--':
                item["gr"] = -1
            item["rw"] = data["rw_num"]
            if item["rw"] == '--':
                item["rw"] = -1
            item["yw"] = data["yw_num"]
            if item["yw"] == '--':
                item["yw"] = -1
            item["rz"] = data["rz_num"]
            if item["rz"] == '--':
                item["rz"] = -1
            item["yz"] = data["yz_num"]
            if item["yz"] == '--':
                item["yz"] = -1
            item["wz"] = data["wz_num"]
            if item["wz"] == '--':
                item["wz"] = -1
            item["qt"] = data["qt_num"]
            if item["qt"] == '--':
                item["qt"] = -1
            yield item
        yield CommitItem()
          





