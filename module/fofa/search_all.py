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
            each_dic = {'ip': each[0], 'port': each[1], 'protocol': each[2], 'country_name': each[3], 'region': each[4],
                        'city': each[5], 'as_organization': each[6], 'host': each[7], 'domain': each[8], 'os': each[9],
                        'server': each[10], 'icp': each[11], 'title': each[12], 'jarm': each[13]}
            info_list.append(each_dic)
        return None
    except Exception as e:
        return f"{str(e)}\n"
