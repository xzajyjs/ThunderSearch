import requests

info_list = []


def quake_host_search(query, page, key):
    global info_list
    info_list = []
    headers = {
        "X-QuakeToken": key,
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "size": int(page) * 10,
    }
    try:
        resp = requests.post("https://quake.360.cn/api/v3/search/quake_host", headers=headers, json=data)
        matches = resp.json()['data']
        for each in matches:
            each_dic = {
                'ip': each.get('ip', None),
                'service_port': each.get('services', {})[0].get('port', None),
                'service_name': each.get('services', {})[0].get('name', None),
                'service_version': each.get('services', {})[0].get('version', None),
                'service_id': each.get('services', {})[0].get('service_id', None),
                'domains': str(each.get('domains', [])).replace(",", ";"),
                'hostname': each.get('hostname', None),
                'os_name': each.get('os_name', None),
                'os_version': each.get('os_version', None),
                'country_en': each.get('location', {}).get('country_en', None),
                'city_en': each.get('location', {}).get('city_en', None)
            }
            info_list.append(each_dic)

    except Exception as e:
        return f"{str(e)}\n"
    return None
