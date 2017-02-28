# armani-scrapy

# README #

This is armani.com scraper written with scrapy framework.
The app has one spider 'main' that can crawl all the products in all categories of chosen region(regions).

To start spider just write (default region 'us'):

```
#!bash

scrapy crawl main
```
You can also set multiple regions at ones:

```
#!bash

scrapy crawl main -a region='us,fr'
```
### Requirements: ###
* scrapy
* demjson
* pandas

full list of requirements can be found at 'requirements.txt'

### Description ###
Since all the product urls, category urls are typical - they can be scraped with the help of LinkExtractor + regex mechanisms. All needed linkextractors combined in list of rules in spider. In such a way our spider can easilly find all the target product pages and scrape each of them.

Each product page can generate one or more parsed product item (item for every combination of 'color' and 'size' of the product (if any)). Also, application parses javascript objects that contains all the initial information about the product and product avaliability. So, we can also know about the avaliability of each variation 'color', 'size' of the product.
The results of the scrapy saved to '{spider.name}_{regions}_items.csv'

At the end of scraping there also small test of the scraped data runs as additional pipeline and save its results to 'armani_test_result.json'. Parameters:
Region: region or list of regions (comma separated)
Size variety: percentage of the items that presented in more than one size
Color variety: percentage of the items that presented in more than one color
Description variety: percentage of the items that presented with description
Total items scraped: total items (with all the variations)
Currency: 'wrong currencies' or 'currency is correct'. It simply checks whether the len of set of input region(regions) is equal to results.csv 'currency' set len. It may show 'wrong currencies' if any row has 'empty' (NaN) value for the 'currency'.
