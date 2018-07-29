# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.pipelines.images import ImagesPipeline
import codecs  # 对文件直接保存或打开成json,类似open函数
import json
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi  # 异步操作
import pymysql.cursors
import pymysql


class ArticleSpyderPipeline(object):  # 数据存储
	def process_item(self, item, spider):
		return item


class ArticleImagePipeline(ImagesPipeline):
	def item_completed(self, results, item, info):
		if "front_image_url" in item:  # 从item中判断item中是否有front_image_url字段(item是一个字典)
			for _, value in results:  # 从spider中接收到的result是一个list,元素是turple(bool,dict)
				image_file_path = value["path"]  # 获取路径
				item["front_image_path"] = image_file_path

		return item


class JsonWithEncodingPipiline(object):
	''' 自定义方式json导出 将spider抓取到的item转化成json格式保存到本地'''

	def __init__(self):
		'''初始化file:打开文件'''
		self.file = codecs.open("article.json", "w", encoding="utf-8")  # 在根目录下创建article.json文件

	def process_item(self, item, spider):
		'''将item文件转换成json后写入到file'''
		lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
		self.file.write(lines)
		return item

	def spider_closed(self, spider):
		'''关闭file'''
		self.file.close()


class JsonExporterPipeline(object):
	'''scrapy自带方式:json export导出json文件'''

	def __init__(self):
		self.file = open("articleexport.json", "wb")  # 创建json文件，设定文件操作权限
		self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
		self.exporter.start_exporting()  #

	def close_spider(self, spider):
		self.exporter.finish_exporting()
		self.file.close()

	def process_item(self, item, spider):
		self.exporter.export_item(item)
		return item


class MysqlPipeline(object):
	'''数据量不是很大的时候使用同步mysql插入'''

	def __init__(sel):
		try:
			self.conn = pymysql.connect(host='localhost',
			                            user='root',
			                            password='myf11040821',
			                            db='article_spider',
			                            charset='utf8mb4',
			                            cursorclass=pymysql.cursors.DictCursor
			                            )
		except Exception as e:
			print(e)
		self.cursor = self.conn.cursor()

	def process_item(self, item, spider):
		try:
			sql = "insert into article(title, create_date, url, url_md5_id,front_image_url,comment_nums,fav_nums,tags,content) VALUES( %s, %s,%s,%s, %s, %s,%s,%s,%s) "
			self.cursor.execute(sql, (
				item["title"], item["create_date"], item["url"], item['url_md5_id'], item["front_image_url"],
				item["comment_nums"], item["fav_nums"], item["tags"], item['content'])
			                    )
			self.conn.commit()
		except Exception as e:
			print(e)


class MysqlTwisedPipeline(object):
	'''使用scrapy自带异步数据库连接池方法实现异步插入'''

	def __init__(self, dbpool):
		self.dbpool = dbpool

	@classmethod
	def from_settings(cls, settings):
		conn_args = dict(
			host=settings["MYSQL_HOST"],
			db=settings["MYSQL_DBNAME"],
			user=settings["MYSQL_USER"],
			password=settings["MYSQL_PASSWORD"],
			charset='utf8',
			cursorclass=pymysql.cursors.DictCursor
		)
		dbpool = adbapi.ConnectionPool("pymysql", **conn_args)  # 构建mysql数据库--'pymysql'通过反射解析到模块
		return cls(dbpool)

	def process_item(self, item, spider):
		'''使用twisted将mysql插入变成异步操作'''
		query = self.dbpool.runInteraction(self.do_insert, item)
		query.addErrback(self.handle_error)  # 处理异常

	def do_insert(self, cursor, item):
		'''插入mysql'''
		sql = '''insert into article(title, create_date, url, url_md5_id,front_image_url,comment_nums,fav_nums,tags,vote_num) " \
		      VALUES( %s, %s,%s,%s, %s, %s,%s,%s,%s) '''
		try:
			cursor.execute(sql, (
				item["title"], item["create_date"], item["url"], item['url_md5_id'], item["front_image_url"],
				item["comment_nums"], item["fav_nums"], item["tags"], item['vote_num'])
			               )
		except Exception as e:
			print(e)

	def handle_error(self, failure):
		# 处理异步插入的异常
		print(failure)
