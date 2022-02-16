import requests
from concurrent.futures import ThreadPoolExecutor

info_list = []
headers = {}

def domain_ip(query, page, thread):
    global info_list
    info_list = []
    with ThreadPoolExecutor(thread) as t:
        for i in range(1,int(page)+1):
            t.submit(domain_ip_threadpool, query=query, page=i)
    return ("End of search.\n")

def domain_ip_threadpool(query, page):
    url = f'https://api.zoomeye.org/domain/search?q={query}&type=0&page={page}'
    print(url)
    try:
        resp = requests.get(url, headers=headers)
        for each in resp.json()['list']:
            each_dic = {}
            try:
                each_dic['ip'] = each['ip']
            except:
                each_dic['ip'] = None
            each_dic['name'] = each['name']
            info_list.append(each_dic)
    except Exception as e:
        if str(e.message) == 'resp':
            return ('[-] info : account was break, excceeding the max limitations\n')
        else:
            return (f'[-] info : {str(e.message)}\n')