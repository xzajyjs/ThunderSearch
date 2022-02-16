import requests
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
    url = f'https://api.zoomeye.org/host/search?query={query}&page={page}&sub_type=v4&facets=app,os'
    print(url)
    try:
        matches = requests.get(url, headers=headers).json()
        for each in matches['matches']:
            each_dic = {}
            each_dic['ip'] = each['ip']
            each_dic['port'] = each['portinfo']['port']
            each_dic['country'] = each['geoinfo']['country']['names']['en']
            each_dic['os'] = each['portinfo']['os']
            each_dic['hostname'] = each['portinfo']['hostname']
            
            info_list.append(each_dic)
    except Exception as e:
        if str(e.message) == 'matches':
            return ('[-] info : account was break, excceeding the max limitations\n')
        else:
            return (f'[-] info : {str(e.message)}\n')