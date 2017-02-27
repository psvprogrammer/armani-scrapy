
import demjson, json

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader.processors import Join, MapCompose, TakeFirst
from armani.items import ArmaniItem, ArmaniProductLoader
from scrapy.exceptions import CloseSpider
from demjson import JSONDecodeError
from datetime import datetime


class MainSpider(CrawlSpider):
    name = 'main'

    def __init__(self, region='us', *args, **kwargs):
        super(MainSpider, self).__init__(*args, **kwargs)

        self.allowed_domains = ['armani.com']

        self._regions = region.split(',')
        self._item_page_re = '_cod.*?\.html$'

        self.rules = []
        for reg in self._regions:
            region_url = 'http://www.armani.com/' + reg
            self.start_urls.append(region_url)
            region_url_re = r'{}\/.*?$'.format(
                region_url.replace('.', '\.').replace('/', '\/')
            )
            self.rules.extend([
                Rule(LinkExtractor(allow=region_url_re,
                                   deny=self._item_page_re), follow=True),
                Rule(LinkExtractor(allow='\*?\/{}\/.*?\/onlinestore\/'.format(
                    reg), deny=self._item_page_re), follow=True),
                Rule(LinkExtractor(allow='/*?\/{}\/.*?{}'.format(
                    reg, self._item_page_re)), callback='parse_item'),
            ])
        self.rules.append(
            Rule(LinkExtractor(allow='\/searchresult*',
                               deny=self._item_page_re), follow=True),
        )
        super(MainSpider, self)._compile_rules()

    def _get_js_objects(self, response):
        js_item_obj = response.xpath('//script'). \
            re(r'(?<=jsoninit_item=)([\w\W ][^;]+)(?=;)')
        if len(js_item_obj) > 0:
            js_item_obj = js_item_obj[0]
        else:
            js_item_obj = None

        js_availability_obj = response.xpath('//script'). \
            re(r'(?<=jsoninit_availability=)([\w\W ][^;]+)(?=;)')
        if len(js_availability_obj) > 0:
            js_availability_obj = js_availability_obj[0]
        else:
            js_availability_obj = None

        if js_item_obj is not None\
                and js_availability_obj is not None:
            try:
                item_data = demjson.decode(js_item_obj)
                item_availability = demjson.decode(js_availability_obj)
            except JSONDecodeError as err:
                self.logger.critical('Error parsing js objects at page url: ' +
                                     response.url + '\n' + err.message)
                # raise CloseSpider()
                return None, None
        return item_data, item_availability

    def _get_item_variation_quantity(self, color_id, size_id,
                                     item_data, item_availability):
        color_id = color_id.replace('Colors:', '')
        size_id = size_id.replace('SizeW:', '')

        try:
            item_cod8 = int(item_data['CURRENTITEM']['code8'])
        except (KeyError, ValueError) as err:
            self.logger.critical('Error parsing item data: ' + err)
            return 0

        try:
            item_availability = item_availability[item_cod8]
        except KeyError as err:
            self.logger.critical('Error parsing item availability: ' + err)
            return 0

        try:
            quantity_dict_list = item_availability['Quantity']
        except KeyError as err:
            self.logger.critical('Error parsing item quantity list: ' + err)
            return 0

        for variation_dict in quantity_dict_list:
            if variation_dict['ColorId'] == color_id and \
                            variation_dict['SizeW'] == size_id:
                return variation_dict['Quantity']
        return 0

    def _get_colors(self, response):
        colors = {}
        color_ids = response.xpath(
            '//ul[@class="Colors"]/li/a/@data-selection').extract()
        for color_id in color_ids:
            color = response.xpath(
                '//ul[@class="Colors"]/li/a[@data-selection='
                '"{}"]/@title'.format(color_id)
            ).extract_first()
            colors[color_id] = color
        return colors

    def _get_sizes(self, response):
        sizes = {}
        size_ids = response.xpath(
            '//ul[@class="SizeW"]/li/a/@data-selection').extract()
        for size_id in size_ids:
            size = response.xpath(
                '//ul[@class="SizeW"]/li/a[@data-selection='
                '"{}"]/@title'.format(size_id)
            ).extract_first()
            sizes[size_id] = size
        return sizes

    def _load_item(self, response):
        start_time = datetime.now()
        self._item = ArmaniProductLoader(item=ArmaniItem(), response=response)
        self._item.add_xpath('name', '//h1[@class="productName"]/text()')
        self._item.add_xpath('price', '//span[@class="priceValue"]/text()')
        self._item.add_xpath('currency', '//span[@class="currency"]/text()')

        self._item.add_css('category', 'li.selected>a::text', Join('->'))
        self._item.add_value('category', ' (', Join(''))
        self._item.add_xpath('category',
                             '//li[@class="selected leaf"]/a/@href', Join(''))
        self._item.add_value('category', ')', Join(''))

        self._item.add_xpath('sku', '//span[@class="MFC"]/text()')

        # parse region from url
        start_pos = response.url.find('.com') + 5
        region = response.url[start_pos:start_pos+2]
        self._item.add_value('region', region)

        self._item.add_xpath('description',
                             '//ul[@class="descriptionList"]/li/text()',
                             Join(', '))
        self._item.add_value('url', response.url)

        # getting javascript object from page
        item_data, item_availability = self._get_js_objects(response)

        # generate item for each possible variation of color and size
        colors, sizes = self._get_colors(response), self._get_sizes(response)
        for color_id, color_value in colors.items():
            self._item.replace_value('color', color_value)
            for size_id, size_value in sizes.items():
                self._item.replace_value('size', size_value)

                # getting availability
                quantity = self._get_item_variation_quantity(
                    color_id, size_id, item_data, item_availability
                )
                if quantity > 0:
                    self._item.replace_value('available', 'yes')
                else:
                    self._item.replace_value('available', 'no')

                self._item.replace_value(
                    'scan_time', (datetime.now() - start_time).total_seconds()
                )
                yield self._item.load_item()
                start_time = datetime.now()

    def parse_item(self, response):
        self.logger.info('Link extractor parse_item: ' + response.url)
        for item in self._load_item(response):
            yield item
