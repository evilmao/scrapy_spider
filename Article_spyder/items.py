# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy
from scrapy.loader.processors import MapCompose,TakeFirst,Join #对item_loader的值进行后期处理
import datetime
from scrapy.loader import ItemLoader
import re


class ArticleSpyderItem(scrapy.Item):
	# define the fields for your item here like:
	# name = scrapy.Field()
	pass


def date_convert_str(value):
	'''对时间进行转换'''
	try:  # 时间转换
		create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
	except Exception as e:
		create_date = datetime.datetime.now().date()
	return create_date

def get_nums(value):
	match = re.match(".*?(\d+).*", value)
	if match:
		nums = int(match.group(1))
	else:  # 当评论条数为0的时候
		nums = 0
	return nums

def return_value(value):
	'''当使用默认输出方式时，为了不覆盖原始的方法'''
	return value

class JobboleArticleItem(scrapy.Item):
	title = scrapy.Field()
	create_date = scrapy.Field(
		input_processor=MapCompose(date_convert_str),   # 时间转换
	)
	url = scrapy.Field()                                # url是个变长
	url_md5_id = scrapy.Field()                         # 将url,MD5后变成定常
	front_image_url = scrapy.Field(
		output_processor=MapCompose(return_value)       # 覆盖默认输出格式
	)
	front_image_path = scrapy.Field()                    # 本地图片存放路径
	comment_nums = scrapy.Field(
		input_processor=MapCompose(get_nums)             # 正则处理数字
	)
	fav_nums = scrapy.Field(
		input_processor=MapCompose(get_nums)
	)
	tags = scrapy.Field(
		output_processor=Join(',')                      # 对tags进行拼接
	)
	content = scrapy.Field()
	vote_num = scrapy.Field()

class ArticleItemLoader(ItemLoader):
	'''自定义item loader集成ItemLoader类
	- 定义属性--item字段默认输出格式，类似对css选择器执行extract_fisrt()
	- 将默认输出变成list
	'''
	default_output_processor = TakeFirst()
