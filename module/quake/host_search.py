import requests

info_list = []
session = requests.Session()


def quake_host_search(query, page, key):
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
        resp = session.post("https://quake.360.cn/api/v3/search/quake_host",headers=headers,json=data)
        matches = resp.json()['data']
        # print(len(matches))
        for each in matches:
            # print(each,"\n\n\n")
            each_dic = {}
            each_dic['ip'] = each['ip']
            each_dic['service_port'] = each['services'][0]['port']
            each_dic['service_name'] = each['services'][0]['name']
            each_dic['service_version'] = each['services'][0]['version']
            each_dic['service_id'] = each['services'][0]['service_id']
            each_dic['domains'] = str(each['domains']).replace(",",";")
            each_dic['hostname'] = each['hostname']
            each_dic['os_name'] = each['os_name']
            each_dic['os_version'] = each['os_version']
            each_dic['country_en'] = each['location']['country_en']
            each_dic['city_en'] = each['location']['city_en']
            info_list.append(each_dic)

    except Exception as e:
        return f"{str(e)}\n"
    return None