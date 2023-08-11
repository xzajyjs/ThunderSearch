import requests
from concurrent.futures import ThreadPoolExecutor
import threading

info_list = []
headers = {}
session = requests.Session()
lock = threading.Lock()


def web_search(query, page, thread):
    global info_list
    info_list = []
    with ThreadPoolExecutor(thread) as t:
        return_info = []
        for i in range(1, int(page) + 1):
            return_info.append(t.submit(web_search_threadpool, query=query, page=i))

    for res in return_info:
        if res.result() is not None:
            return res.result()
    return None


def web_search_threadpool(query, page):
    url = f'https://api.zoomeye.org/web/search?query={query}&page={page}'
    try:
        matches = requests.get(url, headers=headers).json()
        if matches['total'] == 0:
            return 'Total: 0'
        if "'error': '" in matches:
            return matches['message']
        for each in matches['matches']:
            each_dic = {
                'ip': ";".join(each.get('ip', [])),
                'site': each.get('site', None),
                'title': each.get('title', None),
                'city': each.get('geoinfo', {}).get('city', {}).get('names', {}).get('en', None),
                'country': each.get('geoinfo', {}).get('country', {}).get('names', {}).get('en', None),
                'continent': each.get('geoinfo', {}).get('continent', {}).get('names', {}).get('en', None),
                'isp': each.get('geoinfo', {}).get('isp', None)
            }
            with lock:
                info_list.append(each_dic)
        return None
    except Exception as e:
        return f"{str(e)}\n"
