# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
from urllib import parse
from Article_spyder.items import JobboleArticleItem,ArticleItemLoader
from Article_spyder.utils.common import make_md5
import datetime
from scrapy.loader import ItemLoader   #通过loader对item进行操作


class JobboleSpider(scrapy.Spider):
	name = 'jobbole'
	allowed_domains = ['blog.jobbole.com']
	start_urls = ["http://blog.jobbole.com/all-posts/"]

	def parse(self, response):
		'''
		1.获取文章列表中的文章url,并交给scrapy解析函数进行具体字段的解析
		2.获取下一页的所有url,交给scrapy进行下载，下载完成后交给parse
		'''
		# article_urls = response.css("#archive .floated-thumb .post-thumb a::attr(href)").extract() #提取到所有的当前页面文章的urls
		article_css_nodes = response.css("#archive .floated-thumb .post-thumb a ")  # 页面提取所有文章的urls所在a的标签节点
		for article_node in article_css_nodes:
			front_image_url = article_node.css("img::attr(src)").extract_first("")  # 获取到每篇blog的封面图片url
			article_url = article_node.css("::attr(href)").extract_first("")  # 重新获取blog的url

			# yield将Request实例化传递给scrapy,调用Twised异步
			yield Request(url=parse.urljoin(response.url, article_url), meta={"front_image_url": front_image_url},
			              callback=self.parse_article_detail)  # 回掉函数，将解析大的url交给解析blog详情函数

		# 提取下一页的所有blogs_urls交给scrapy
		next_page_urls = response.css(".next.page-numbers::attr(href)").extract_first("")  # 同级的css节点没有空格，直接用.链接
		if next_page_urls:
			yield Request(url=parse.urljoin(response.url, next_page_urls), callback=self.parse)

	def parse_article_detail(self, response):
		'''提取具体blog页面的字段'''

		# -------------------------通过xpath进行查找------------------------------
		# title = response.xpath("//div[@class='entry-header']/h1/text()").extract_first(
		# 	"")  # 定位title--extract_first()方法可以避免所取数字为空出现的异常
		# create_data = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract()[0].strip().replace(".",
		#                                                                                                             "").strip()  # 定位创建日期
		# vote = response.xpath("//span[contains(@class,'vote-post-up')]/h10/text()").extract()[0]  # 定位vote
		# fav_nums = response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract()[0]  # 定位收藏
		#
		# match = re.match(".*?(\d+).*", fav_nums)
		# if match:
		# 	fav_nums = int(match.group(1))
		#
		# comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]  # 提取出comments
		# match_re = re.match(".*?(\d+).*", comment_nums)
		# if match:
		# 	comment_nums = int(match_re.group(1))
		# else:  # 当评论条数为0的时候
		# 	comment_nums = 0
		# content = response.xpath("//div[@class='entry']").extract()[0]  # 定位正文
		# tag_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()  # 标签
		# tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
		# tags = ",".join(tag_list)

		# ----------------------------通过css选择器定位----------------------------

		# title = response.css(".entry-header h1::text").extract()
		# create_date = response.css(".entry-meta-hide-on-mobile::text").extract()[0].strip().replace("·", " ").strip()
		# vote_num = response.css(".vote-post-up h10::text").extract_first("")
		# fav_nums = response.css(".bookmark-btn::text").extract()[0]
		#
		# match = re.match(".*?(\d+).*", fav_nums)
		# if match:
		# 	fav_nums = int(match.group(1))
		# else:
		# 	fav_nums = 0
		#
		# comment_nums = response.css("span.hide-on-480::text").extract()[0]
		# match = re.match(".*?(\d+).*", comment_nums)
		# if match:
		# 	comment_nums = int(match.group(1))
		# else:  # 当评论条数为0的时候
		# 	comment_nums = 0
		#
		# content = response.css(".entry").extract()[0]
		# tag_list = response.css(".entry-meta-hide-on-mobile a[href^='http']::text").extract() #定位blog标签
		# tags = ",".join(tag_list)  # 标签拼接

		#-----------------item填充--------------------
		# article_item["title"] = title
		# article_item["url"] = response.url
		# try:                                                                 # 时间转换
		# 	create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
		# except Exception as e:
		# 	create_date = datetime.datetime.now().date()
		# article_item["create_date"] = create_date
		# article_item["front_image_url"] = [front_image_url]
		# article_item["comment_nums"] = comment_nums
		# article_item["fav_nums"] = fav_nums
		# article_item["tags"] = tags
		# article_item["content"] = content
		# article_item["url_md5_id"] = make_md5(response.url)                         # 调用make_md5函数对url进行处理
		# article_item['vote_num']= int(vote_num)

		#----------通过iterm_loader直接将页面解析的字段填充到item中
		article_item = JobboleArticleItem()                                           # 实例化item
		front_image_url = response.meta.get("front_image_url", "")                    # 获取封面图

		item_loader = ArticleItemLoader(item=JobboleArticleItem(),response=response)  # 实例化ArticleItemLoader(自定义itemloader),调用默认输出方式,对item进行处理
		item_loader.add_css('title',".entry-header h1::text")                         # 第一个参数为item字段，后一个参数为css路径
		item_loader.add_value('url',response.url)                                     # 第一个参数为item字段，后一个为value
		item_loader.add_css('create_date','.entry-meta-hide-on-mobile::text')
		item_loader.add_value('front_image_url',[front_image_url])                    # 本来就是一个list类型,默认输出取第一个值就变成了str
		item_loader.add_css('comment_nums','span.hide-on-480::text')
		item_loader.add_css('fav_nums','.bookmark-btn::text')
		item_loader.add_css('tags',".entry-meta-hide-on-mobile a[href^='http']::text")
		item_loader.add_css('content','.entry')
		item_loader.add_value('url_md5_id', make_md5(response.url))
		item_loader.add_css('vote_num','.vote-post-up h10::text')

		article_item = item_loader.load_item()                                         # 实例化item_loader,调用load_item方法将item加载article_item中
		yield article_item                                                             # 使用yield将内容传递给pipelines

		pass
