import requests

info_list = []
session = requests.Session()


def quake_service_search(query, page, key):
    global info_list
    info_list = []
    headers = {
        "X-QuakeToken": key,
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "size": int(page)*10,
    }
    try:
        resp = session.post("https://quake.360.cn/api/v3/search/quake_service",headers=headers,json=data)
        matches = resp.json()['data']
        for each in matches:
            print(each['service']['name'])
            each_dic = {}
            each_dic['ip'] = each['ip']
            each_dic['port'] = each['port']
            each_dic['org'] = each['org']
            each_dic['hostname'] = each['hostname']
            each_dic['service_name'] = each['service']['name']
            try:
                each_dic['service_title'] = each['service'][each_dic['service_name']]['title']
                each_dic['service_server'] = each['service'][each_dic['service_name']]['server']
            except Exception as e:
                each_dic['service_title'] = ""
                each_dic['service_server'] = ""
            each_dic['transport'] = each['transport']
            each_dic['os_name'] = each['os_name']
            each_dic['country_en'] = each['location']['country_en']
            each_dic['city_en'] = each['location']['city_en']
            each_dic['os_version'] = each['os_version']
            info_list.append(each_dic)  

    except Exception as e:
        return f"{str(e)}\n"
    return None