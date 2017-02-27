# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pandas as pd
import json

from scrapy import signals
from scrapy.contrib.exporter import CsvItemExporter


class CSVArmaniPipeline(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        file = open(
            '{}({})_items.csv'.format(spider.name, ','.join(spider._regions)),
            'w+b'
        )
        self.files[spider] = file
        self.exporter = CsvItemExporter(file)
        self.exporter.fields_to_export = [
            'sku',
            'name',
            'price',
            'currency',
            'color',
            'size',
            'available',
            'region',
            'category',
            'description',
            'scan_time',
            'url',
        ]
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class ArmaniTestResults(object):
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def get_color_size_fill(self, df):
        color_items, size_items, desc_items = 0.0, 0.0, 0.0
        total = float(len(set(df['sku'])))
        for sku in set(df['sku']):
            sku_filter = df[df['sku'].isin([sku])]
            if len(set(sku_filter['color'])) > 1:
                color_items += 1
            if len(set(sku_filter['size'])) > 1:
                size_items += 1

        for ind, row in df.iterrows():
            if row['description'].strip() != '':
                desc_items += 1

        color_fill = color_items / total * 100
        size_fill = size_items / total * 100
        desc_fill = desc_items / len(df) * 100

        return color_fill, size_fill, desc_fill

    def run_test(self, spider):
        df = pd.read_csv(
            '{}({})_items.csv'.format(spider.name, ','.join(spider._regions))
        )
        item_total = len(df)
        currency_len = len(spider._regions)
        if len(set(df['currency'])) != currency_len:
            currency = 'wrong currencies'
        else:
            correct_currencies = set()
            for region in spider._regions:
                if region == 'us':
                    correct_currencies.add('$')
                if region == 'fr':
                    correct_currencies.add('EUR')
            if set(df['currency']) == correct_currencies:
                currency = 'currency is correct'
            else:
                currency = 'wrong currencies'

        color_fill, size_fill, desc_fill = self.get_color_size_fill(df)

        result = {
            'Total items scraped': item_total,
            'Currency': currency,
            'Region': ','.join(spider._regions),
            'Color variety': '{0:.2f}'.format(color_fill),
            'Size variety': '{0:.2f}'.format(size_fill),
            'Description variety': '{0:.2f}'.format(desc_fill),
        }

        with open('armani_test_result.json', 'w') as file:
            json.dump(result, file)

    def spider_opened(self, spider):
        pass
        # self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.run_test(spider)
        # self.exporter.finish_exporting()
