import os, time, requests, json
from verify import send_code, send_radar

base_url = "https://lnt.xmu.edu.cn"
headers = {
    "User-Agent":(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def a(data, session):
    data_empty = {'rollcalls': []}
    result = p(data, session)
    if False in result: return data_empty
    else: return data

def c():
    # clear the console
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def d(data):
    rollcalls = data['rollcalls']
    result = []
    if rollcalls:
        rollcall_count = len(rollcalls)
        for rollcall in rollcalls:
            result.append(
                {
                    'course_title': rollcall['course_title'],
                    'created_by_name': rollcall['created_by_name'],
                    'department_name': rollcall['department_name'],
                    'is_expired': rollcall['is_expired'],
                    'is_number': rollcall['is_number'],
                    'is_radar': rollcall['is_radar'],
                    'rollcall_id': rollcall['rollcall_id'],
                    'rollcall_status': rollcall['rollcall_status'],
                    'scored': rollcall['scored'],
                    'status': rollcall['status']
                }
            )
    else:
        rollcall_count = 0
    return rollcall_count, result

def p(data, session):
    count, rollcalls = d(data)
    answer_status = [False for _ in range(count)]
    if count:
        print(time.strftime("%H:%M:%S", time.localtime()), f"New rollcall(s) found!\n")
        for i in range(count):
            print(f"{i+1} of {count} :")
            print(f"Course name：{rollcalls[i]['course_title']},rollcall created by {rollcalls[i]['department_name']} {rollcalls[i]['created_by_name']}.")
            if rollcalls[i]['is_radar']:
                temp_str = "Radar rollcall"
            elif rollcalls[i]['is_number']:
                temp_str = "Number rollcall"
            else:
                temp_str = "QRcode rollcall"
            print(f"rollcall type：{temp_str}\n")
            if (rollcalls[i]['status'] == 'absent') & (rollcalls[i]['is_number']) & (not rollcalls[i]['is_radar']):
                if send_code(session, rollcalls[i]['rollcall_id']):
                    answer_status[i] = True
                else:
                    print("Answering failed.")
            elif rollcalls[i]['status'] == 'on_call_fine':
                print("Already answered.")
                answer_status[i] = True
            elif rollcalls[i]['is_radar']:
                if send_radar(session, rollcalls[i]['rollcall_id']):
                    answer_status[i] = True
                else:
                    print("Answering failed.")
            else:
                # todo: qrcode rollcall
                print("Answering failed.")
    return answer_status

def t(name):
    if time.localtime().tm_hour < 12 and time.localtime().tm_hour >= 5:
        greeting = "Good morning"
    elif time.localtime().tm_hour < 18 and time.localtime().tm_hour >= 12:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return f"{greeting}, {name}!"


def s(sess: requests.Session, path: str):
    try:
        cj_divt = requests.utils.dict_from_cookiejar(sess.cookies)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cj_divt, f)
    except Exception:
        pass

def l(sess: requests.Session, path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            cj_dict = json.load(f)
        sess.cookies = requests.utils.cookiejar_from_dict(cj_dict)
        return True
    except Exception:
        return False

def v(sess: requests.Session) -> dict:
    try:
        resp = sess.get(f"{base_url}/api/profile", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "name" in data:
                return data
    except Exception:
        pass
    return {}