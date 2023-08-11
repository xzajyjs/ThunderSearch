import requests
import base64

total_num = 0
info_list = []
session = requests.session()


def fofa_search(email, key, query, size):
    global info_list, total_num
    info_list = []
    qbase64 = base64.b64encode(query.encode('utf8'))
    params = {
        'email': email,
        'key': key,
        'qbase64': qbase64,
        'fields': 'ip,port,protocol,country_name,region,city,as_organization,host,domain,os,server,icp,title,jarm',
        'page': 1,
        'size': size
    }
    try:
        resp = session.get('https://fofa.info/api/v1/search/all', data=params)
        if resp.json()['error']:
            return resp.json()['errmsg']
        data = resp.json()['results']
        total_num = len(data)
        for each in data:
            each_dic = {
                'ip': each.get(0, None),
                'port': each.get(1, None),
                'protocol': each.get(2, None),
                'country_name': each.get(3, None),
                'region': each.get(4, None),
                'city': each.get(5, None),
                'as_organization': each.get(6, None),
                'host': each.get(7, None),
                'domain': each.get(8, None),
                'os': each.get(9, None),
                'server': each.get(10, None),
                'icp': each.get(11, None),
                'title': each.get(12, None),
                'jarm': each.get(13, None)
            }
            info_list.append(each_dic)
        return None
    except Exception as e:
        return f"{str(e)}\n"
