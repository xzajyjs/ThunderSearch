import requests

info_list = []


def quake_service_search(query, page, key):
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
        resp = requests.post("https://quake.360.cn/api/v3/search/quake_service", headers=headers, json=data)
        if resp.status_code == 401:
            return "API-KEY error."
        matches = resp.json()['data']
        for each in matches:
            each_dic = {
                'ip': each.get('ip', None),
                'port': each.get('port', None),
                'org': each.get('org', None),
                'hostname': each.get('hostname', None),
                'service_name': each.get('service', {}).get('name', None),
                'service_title': each.get('service', {}).get(each.get('service', {}).get('name', None), {}).get('title',
                                                                                                                None),
                'service_server': each.get('service', {}).get(each.get('service', {}).get('name', None), {}).get(
                    'server', None),
                'transport': each.get('transport', None),
                'os_name': each.get('os_name', None),
                'country_en': each.get('location', {}).get('country_en', None),
                'city_en': each.get('location', {}).get('city_en', None),
                'os_version': each.get('os_version', None)
            }

            info_list.append(each_dic)

    except Exception as e:
        return f"{str(e)}\n"
