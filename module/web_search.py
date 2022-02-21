import requests
from concurrent.futures import ThreadPoolExecutor

info_list = []
headers = {}

def web_search(query, page, thread):
    global info_list
    info_list = []
    with ThreadPoolExecutor(thread) as t:
        for i in range(1,int(page)+1):
            t.submit(web_search_threadpool, query=query, page=i)
    return ("End of search.\n")

def web_search_threadpool(query, page):
    url = f'https://api.zoomeye.org/web/search?query={query}&facets=app,os&page={page}'
    print(url)
    try:
        matches = requests.get(url, headers=headers).json()
        for each in matches['matches']:
            each_dic = {}
            each_dic['ip'] = ";".join(each['ip'])
            each_dic['site'] = each['site']
            each_dic['city'] = each['geoinfo']['city']['names']['en']
            each_dic['country'] = each['geoinfo']['country']['names']['en']
            each_dic['continent'] = each['geoinfo']['continent']['names']['en']
            each_dic['isp'] = each['geoinfo']['isp']

            info_list.append(each_dic)
    except Exception as e:
        if str(e.message) == 'matches':
            return ('[-] info : account was break, excceeding the max limitations\n')
        else:
            return (f'[-] info : {str(e.message)}\n')