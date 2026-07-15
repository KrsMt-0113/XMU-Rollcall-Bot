import time
from .verify import (
    attendance_threshold_reached,
    send_code,
    send_radar,
    send_self_registration,
)

def process_rollcalls(data, session, attendance_threshold=0.2):
    """处理签到数据"""
    data_empty = {'rollcalls': []}
    result = handle_rollcalls(data, session, attendance_threshold)
    if False in result:
        return data_empty
    else:
        return data

def extract_rollcalls(data):
    """提取签到信息"""
    rollcalls = data.get('rollcalls', [])
    result = []
    if rollcalls:
        rollcall_count = len(rollcalls)
        for rollcall in rollcalls:
            details = rollcall.get('rollcall')
            if not isinstance(details, dict):
                details = rollcall

            def value(key, default=None):
                outer_value = rollcall.get(key)
                if outer_value is not None:
                    return outer_value
                return details.get(key, default)

            result.append({
                'course_title': value('course_title', ''),
                'created_by_name': value('created_by_name', ''),
                'department_name': value('department_name', ''),
                'is_expired': value('is_expired', False),
                'is_number': value('is_number', False),
                'is_radar': value('is_radar', False),
                'rollcall_id': value('rollcall_id', value('id')),
                'rollcall_status': value('rollcall_status', ''),
                'scored': value('scored', False),
                'source': value('source', ''),
                'type': value('type', ''),
                'status': value('status', '')
            })
    else:
        rollcall_count = 0
    return rollcall_count, result

def handle_rollcalls(data, session, attendance_threshold=0.2):
    """处理签到流程"""
    count, rollcalls = extract_rollcalls(data)
    answer_status = [False for _ in range(count)]

    if count:
        print(time.strftime("%H:%M:%S", time.localtime()), "New rollcall(s) found!\n")
        for i in range(count):
            print(f"{i+1} of {count}:")
            print(f"Course name: {rollcalls[i]['course_title']}, rollcall created by {rollcalls[i]['department_name']} {rollcalls[i]['created_by_name']}.")

            is_self_registration = (
                rollcalls[i]['source'] == 'manual'
                and rollcalls[i]['type'] == 'self_registration'
            )

            if is_self_registration:
                temp_str = "Self-registration rollcall"
            elif rollcalls[i]['is_radar']:
                temp_str = "Radar rollcall"
            elif rollcalls[i]['is_number']:
                temp_str = "Number rollcall"
            else:
                temp_str = "QRcode rollcall"
            print(f"Rollcall type: {temp_str}\n")

            if rollcalls[i]['status'] in ('on_call', 'on_call_fine'):
                print("Already answered.")
                answer_status[i] = True
                continue

            is_number_rollcall = (
                rollcalls[i]['status'] == 'absent'
                and rollcalls[i]['is_number']
                and not rollcalls[i]['is_radar']
            )
            is_supported = (
                is_self_registration
                or is_number_rollcall
                or rollcalls[i]['is_radar']
            )
            if not is_supported:
                print("Answering failed. QRcode rollcall not supported yet.")
                continue

            threshold_reached, details = attendance_threshold_reached(
                session,
                rollcalls[i]['rollcall_id'],
                attendance_threshold,
            )
            if not threshold_reached:
                continue

            if is_self_registration:
                if send_self_registration(session, rollcalls[i]['rollcall_id']):
                    answer_status[i] = True
                else:
                    print("Answering failed.")
            elif is_number_rollcall:
                if send_code(session, rollcalls[i]['rollcall_id'], details):
                    answer_status[i] = True
                else:
                    print("Answering failed.")
            elif rollcalls[i]['is_radar']:
                if send_radar(session, rollcalls[i]['rollcall_id']):
                    answer_status[i] = True
                else:
                    print("Answering failed.")
    return answer_status
