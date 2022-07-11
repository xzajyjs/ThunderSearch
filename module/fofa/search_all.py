import requests
import base64

total_num = 0
info_list = []
session = requests.session()

def fofa_search(email,key,query,size):
    global info_list,total_num
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
        data = resp.json()['results']
        total_num = len(data)
        session.close()
        for each in data:
            each_dic = {}
            each_dic['ip'] = each[0]
            each_dic['port'] = each[1]
            each_dic['protocol'] = each[2]
            each_dic['country_name'] = each[3]
            each_dic['region'] = each[4]
            each_dic['city'] = each[5]
            each_dic['as_organization'] = each[6]
            each_dic['host'] = each[7]
            each_dic['domain'] = each[8]
            each_dic['os'] = each[9]
            each_dic['server'] = each[10]
            each_dic['icp'] = each[11]
            each_dic['title'] = each[12]
            each_dic['jarm'] = each[13]
            info_list.append(each_dic)
        return None
    except Exception as e:
        return e
