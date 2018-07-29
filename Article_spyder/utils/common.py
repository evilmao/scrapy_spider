# -*- coding: utf-8 -*-

import hashlib


def make_md5(url):
	'''对url进行md5处理'''
	if isinstance(url,str): #unicode类型
		url = url.encode("utf8")
	m = hashlib.md5()
	m.update(url)
	return m.hexdigest()


if __name__ =="__main__":
	print(make_md5("https://www.baidu.com"))
