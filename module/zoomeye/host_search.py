import requests
from concurrent.futures import ThreadPoolExecutor
import threading

info_list = []
headers = {}
session = requests.Session()
lock = threading.Lock()


def host_search(query, page, thread):
    global info_list
    info_list = []
    with ThreadPoolExecutor(thread) as t:
        return_info = []
        for i in range(1, int(page) + 1):
            t.submit(host_search_threadpool, query=query, page=i)

    for res in return_info:
        if res.result() is not None:
            return res.result()
    return None


def host_search_threadpool(query, page):
    url = f'https://api.zoomeye.org/host/search?query={query}&page={page}&facets=app,os'
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        matches = resp.json()
        if "'error': '" in str(matches):
            return matches['message']
        for each in matches['matches']:
            title_value = each.get('portinfo', {}).get('title', None)
            # 检查 title_value 是否可迭代（列表或元组）
            if isinstance(title_value, (list, tuple)):
                # 如果可迭代，使用 join 方法连接成字符串
                joined_title = ';'.join(map(str, title_value))
            else:
                # 如果不可迭代，使用原始值（或某个默认值）
                joined_title = str(title_value)
            each_dic = {
                'ip': each.get('ip', None),
                'port': each.get('portinfo', {}).get('port', None),
                'os': each.get('portinfo', {}).get('os', None),
                'app': each.get('portinfo', {}).get('app', None),
                'version': each.get('portinfo', {}).get('version', None),
                # 'title': ';'.join(each.get('portinfo', {}).get('title', None)),
                'title': joined_title,
                'city': each.get('geoinfo', {}).get('city', {}).get('names', {}).get('en', None),
                'country': each.get('geoinfo', {}).get('country', {}).get('names', {}).get('en', None),
                'continent': each.get('geoinfo', {}).get('continent', {}).get('names', {}).get('en', None)
            }
            with lock:
                info_list.append(each_dic)

    except Exception as e:
        return f"{str(e)}\n"
