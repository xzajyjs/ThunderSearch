import shodan

info_list = []


def search(key, query, page):
    global info_list
    info_list = []
    api = shodan.Shodan(key)
    try:
        for i in range(int(page)):
            res_lst = api.search(query, page=i + 1)
            for each in res_lst['matches']:
                each_dic = {
                    'ip': each.get('ip_str', None),
                    'port': each.get('port', None),
                    'country': str(each.get('location', {}).get('country_name', None)).replace(',', '-'),
                    'city': str(each.get('location', {}).get('city', None)).replace(',', '-'),
                    'domains': ';'.join(each.get('domains', [])),
                    'os': str(each.get('os', None)).replace(',', '-'),
                    'title': str(each.get('http', {}).get('title', None)).replace(',', '-'),
                    'product': str(each.get('product', None)).replace(',', '-'),
                    'timestamp': each.get('timestamp', None),
                    'info': str(each.get('info', None)).replace(',', '-'),
                    'isp': each.get('isp', None)
                }
                info_list.append(each_dic)
        print(len(info_list))
        return None
    except Exception as e:
        return f"{str(e)}\n"
