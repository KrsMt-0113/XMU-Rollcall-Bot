import time
from .verify import send_code, send_radar

def process_rollcalls(data, session):
    """处理签到数据"""
    data_empty = {'rollcalls': []}
    result = handle_rollcalls(data, session)
    if False in result:
        return data_empty
    else:
        return data

def extract_rollcalls(data):
    """提取签到信息"""
    rollcalls = data['rollcalls']
    result = []
    if rollcalls:
        rollcall_count = len(rollcalls)
        for rollcall in rollcalls:
            result.append({
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
            })
    else:
        rollcall_count = 0
    return rollcall_count, result

def handle_rollcalls(data, session):
    """处理签到流程"""
    count, rollcalls = extract_rollcalls(data)
    answer_status = [False for _ in range(count)]

    if count:
        print(time.strftime("%H:%M:%S", time.localtime()), f"New rollcall(s) found!\n")
        for i in range(count):
            print(f"{i+1} of {count}:")
            print(f"Course name: {rollcalls[i]['course_title']}, rollcall created by {rollcalls[i]['department_name']} {rollcalls[i]['created_by_name']}.")

            if rollcalls[i]['is_radar']:
                temp_str = "Radar rollcall"
            elif rollcalls[i]['is_number']:
                temp_str = "Number rollcall"
            else:
                temp_str = "QRcode rollcall"
            print(f"Rollcall type: {temp_str}\n")

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
                # TODO: qrcode rollcall
                print("Answering failed. QRcode rollcall not supported yet.")

    return answer_status

