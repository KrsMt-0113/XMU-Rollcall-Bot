import time
from verify import send_code, send_radar

def decode_rollcall(data):
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

def parse_rollcalls(data, driver):
    count, rollcalls = decode_rollcall(data)
    if count:
        print(time.strftime("%H:%M:%S", time.localtime()),f"监测到新的签到活动。\n")
        for i in range(count):
            print(f"第 {i+1} 个，共 {count} 个：")
            print(f"课程名称：{rollcalls[i]['course_title']}")
            print(f"签到创建：{rollcalls[i]['created_by_name']}")
            print(f"签到状态：{rollcalls[i]['rollcall_status']}")
            print(f"是否计分：{rollcalls[i]['scored']}")
            print(f"出勤情况：{rollcalls[i]['status']}")
            if rollcalls[i]['is_radar'] & rollcalls[i]['is_number']:
                temp_str = "数字及雷达签到"
            elif rollcalls[i]['is_radar']:
                temp_str = "雷达签到"
            else:
                temp_str = "数字签到"
            print(f"签到类型：{temp_str}\n")
            if (rollcalls[i]['status'] == 'absent') & (rollcalls[i]['is_number']) & (not rollcalls[i]['is_radar']):
                if send_code(driver, rollcalls[i]['rollcall_id']):
                    print("签到成功！")
                    return True
                else:
                    print("签到失败。")
                    return False
            elif rollcalls[i]['status'] == 'on_call_fine':
                print("该签到已完成。")
                return True
            elif rollcalls[i]['is_radar']:
                if send_radar(driver, rollcalls[i]['rollcall_id']):
                    print("签到成功！")
                    return True
                else:
                    print("签到失败。")
                    return False
            else:
                return False
    else:
        print("当前无签到活动。")
        return False
