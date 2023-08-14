import requests
import base64
import traceback

info_list = []
other_info = {}


def search(key, query, page):
    global info_list
    info_list = []
    query = str(base64.urlsafe_b64encode(query.encode("utf-8")), 'utf-8')
    try:
        for i in range(int(page)):
            url = f"https://hunter.qianxin.com/openApi/search?api-key={key}&search={query}&page={i + 1}&page_size=20&is_web=3"
            resp = requests.get(url)
            # print(resp.json())
            if resp.json()['code'] != 200 or resp.json()['message'] != 'success':
                return f"{str(resp.json()['message'])}\n"
            data = resp.json()['data']
            if i == 0:
                global other_info
                other_info['total'], other_info['consume_quota'], other_info['rest_quota'] = data['total'], data[
                    'consume_quota'].replace('消耗积分：', ''), data['rest_quota'].replace('今日剩余积分：', '')
            for each in data['arr']:
                dic = {
                    'is_risk': each.get('is_risk', None),
                    'url': each.get('url', None),
                    'ip': each.get('ip', None),
                    'port': each.get('port', None),
                    'web_title': each.get('web_title', None),
                    'domain': each.get('domain', None),
                    'is_risk_protocol': each.get('is_risk_protocol', None),
                    'protocol': each.get('protocol', None),
                    'base_protocol': each.get('base_protocol', None),
                    'status_code': each.get('status_code', None),
                    'component': each.get('component', None),
                    'os': each.get('os', None),
                    'company': each.get('company', None),
                    'number': each.get('number', None),
                    'country': each.get('country', None),
                    'province': each.get('province', None),
                    'city': each.get('city', None),
                    'updated_at': each.get('updated_at', None),
                    'is_web': each.get('is_web', None),
                    'as_org': each.get('as_org', None),
                    'isp': each.get('isp', None),
                    # 'banner': each.get('banner', None),
                    'vul_list': each.get('vul_list', None)
                }
                for key, value in dic.items():
                    dic[key] = str(value).replace(',', '-').replace('\n', ' ')

                # print("======================")
                # print(dic)
                # print("======================")

                info_list.append(dic)
        return None
    except Exception:
        return f"{str(traceback.format_exc())}\n"
