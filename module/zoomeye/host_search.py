import requests
import pymysql
from concurrent.futures import ThreadPoolExecutor

info_list = []
headers = {}

def host_search(query, page, thread):
    global info_list
    info_list = []
    with ThreadPoolExecutor(thread) as t:
        for i in range(1,int(page)+1):
            t.submit(host_search_threadpool, query=query, page=i)
    return ("End of search.\n")

def host_search_threadpool(query, page):
    url = f'https://api.zoomeye.org/host/search?query={query}&page={page}&facets=app,os'
    print(url)
    try:
        matches = requests.get(url, headers=headers, timeout=5).json()
        for each in matches['matches']:
            each_dic = {}
            each_dic['ip'] = each['ip']
            each_dic['port'] = each['portinfo']['port']
            each_dic['os'] = each['portinfo']['os']
            each_dic['app'] = each['portinfo']['app']
            each_dic['version'] = each['portinfo']['version']
            each_dic['title'] = each['portinfo']['title']
            if each_dic['title'] != None:
                each_dic['title'] = each_dic['title'][0]
            each_dic['city'] = each['geoinfo']['city']['names']['en']   #城市
            each_dic['country'] = each['geoinfo']['country']['names']['en']     #国家
            each_dic['continents'] = each['geoinfo']['continent']['names']['en']    #大洲
            
            info_list.append(each_dic)
    except Exception as e:
        if str(e.message) == 'matches':
            return ('[-] info : account was break, excceeding the max limitations\n')
        else:
            return (f'[-] info : {str(e.message)}\n')