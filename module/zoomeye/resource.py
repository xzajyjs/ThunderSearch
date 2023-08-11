import requests

headers = {}


def resource(mode):  # user_info
    try:
        resp = requests.get('https://api.zoomeye.org/resources-info', headers=headers)
        if 'error' in str(resp.json()):
            return f"[!] Error: {resp.json()['message']}\n"
        last = resp.json()['resources']['search']
    except Exception as e:
        return str(e)
    else:
        if mode == "easy":
            return f"[!] Your account's Remaining query quota: {last} (this month).\n"
        elif mode == "complete":
            inteval = resp.json()['resources']['interval']
            uname = resp.json()['user_info']['name']
            role = resp.json()['user_info']['role']
            expired_at = resp.json()['user_info']['expired_at']
            remain_free_quota = resp.json()['quota_info']['remain_free_quota']
            remain_pay_quota = resp.json()['quota_info']['remain_pay_quota']
            remain_total_quota = resp.json()['quota_info']['remain_total_quota']
            return (
                f'========= Zoomeye ========\n[+] Name: {uname}\n[+] Role: {role}\n[+] Intevel: {inteval}\n[+] Expired_at: {expired_at}\n[+] Remain_free_quota: {remain_free_quota}\n[+] Remain_pay_quota: {remain_pay_quota}\n[+] Remain_total_quota: {remain_total_quota}\n========================\n')
