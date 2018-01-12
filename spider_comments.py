import json
from json import JSONDecodeError
import requests
import re
import time
import random
import linecache

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36',

}
proxies = None      # 代理ip
count = 1           # 行计数器（ip.txt文件）


# 从ip.txt文本文档中获得ip地址和端口信息，存到字典proxies变量中
def get_proxies():
    global count
    # 获取文本文档的第 count 行信息
    proxy = linecache.getline('ip.txt', count).strip()
    count += 1
    global proxies
    proxies = {'https': 'http://' + proxy}


# 请求url，成功则返回.text，不成功则更换代理后重新请求此url
def get_page(url):
    try:
        global proxies
        response = requests.get(url, headers=headers, proxies=proxies)
        if response.status_code == 200:
            return response.text
        else:
            print('请求不成功，返回状态码为：', response.status_code)
            get_proxies()
            print('更换代理ip', proxies)
            get_page(url)
    except requests.exceptions.ProxyError:
        print('代理出现异常')
        get_proxies()
        print('更换新的代理ip:', proxies)
        get_page(url)
    except Exception:
        print('请求页面异常')
        get_proxies()
        print('更换新的代理ip:', proxies)
        get_page(url)


# 解析JSON格式的数据，迭代生成电影名(title)和电影ID(id)
def parse_moviesID(text):
    try:
        data = json.loads(text)
        if data and 'data' in data.keys():
            # 若键data的值为空列表，则结束爬取
            if data.get('data') == []:
                print('数据为空，爬取结束')
                exit()
            for item in data.get('data'):
                yield {
                    'title': item.get('title'),
                    'id': item.get('id')
                }
    except JSONDecodeError:
        print('JSON解码异常!')
    except Exception:
        print('解析电影ID信息异常')


# 获取电影短评
def parse_comments(data, name):
    try:
        pattern = re.compile('<p class="">(.*?)</p>', re.S)
        comments = re.findall(pattern, data)
        for item in comments:
            save_to_file(item.strip(), name)
    except Exception:
        print('短评解析错误')


# 保存到文本文档，命名为'电影名'.txt
def save_to_file(item, name):
    try:
        with open(name + '.txt', 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            f.close()
    except Exception:
        print('存入文件失败')


def main(number):
    index_url = 'https://movie.douban.com/j/new_search_subjects?sort=T&range=0,10&tags=&start=' + str(number)
    print('正在请求第 %d 页电影ID信息' % (number/20 + 1))
    index_data = get_page(index_url)
    for info in parse_moviesID(index_data):
        title = info['title']
        print('正在请求电影 %s 的评论' % title)
        for page in range(11):
            comments_url = 'https://movie.douban.com/subject/' + str(info['id'])\
                         + '/comments?limit=20&sort=new_score&status=P&percent_type&start=' + str(page * 20)
            print('正在请求第 %d 页评论' % (page + 1))
            comments = get_page(comments_url)
            parse_comments(comments, title)
        print('休息一下')
        time.sleep(random.uniform(2, 4))


if __name__ == '__main__':
    for i in range(499):
        main(i * 20)