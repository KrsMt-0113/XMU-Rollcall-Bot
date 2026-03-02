# from: https://github.com/wilinz/fuck_tronclass_sign/blob/main/parse_sign_qr_code.py

# 定义特殊字符
ta = chr(30)
ea = chr(31)
na = chr(26)
ra = chr(16)
ia = na + "1"
oa = na + "0"

# 辅助函数：将整数转换为 base36 字符串
def to_base36(num):
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if num < 0:
        return "-" + to_base36(-num)
    elif num < 36:
        return chars[num]
    else:
        result = ""
        while num:
            num, rem = divmod(num, 36)
            result = chars[rem] + result
        return result

# aa 对应的对象，key 为各字段名，value 为 index 转换成 base36 后的字符串
aa = { key: to_base36(i) for i, key in enumerate([
    "courseId", "activityId", "activityType", "data", "rollcallId",
    "groupSetId", "accessCode", "action", "enableGroupRollcall", "createUser",
    "joinCourse"
]) }

# ua 对应的对象，key 为各字段名，value 为 na 加上 (index+2) 转为 base36 的字符串
ua = { key: na + to_base36(i + 2) for i, key in enumerate([
    "classroom-exam", "feedback", "vote"
]) }

# ca 为 aa 的键值对反转后的字典
ca = { v: k for k, v in aa.items() }
# sa 为 ua 的键值对反转后的字典
sa = { v: k for k, v in ua.items() }

def parse_sign_qr_code(t):
    """
    解析字符串 t，将其按照分隔符处理后，返回一个字典对象。

    分隔逻辑：
      - 首先以 "!" 分割字符串，再过滤掉空项
      - 对每一段，再以 "~" 分割为 key 和 value 两部分
      - key 使用 ca 映射（若存在对应关系），否则原样使用
      - value 的处理：
          * 如果以 na 开头：
              - 若等于 ia，则返回 True
              - 否则若不等于 oa，则返回 sa 映射中的值（若存在），否则原样返回
              - 若等于 oa，则返回 False
          * 如果以 ra 开头：
              - 截取 ra 之后的部分，用 "." 分割，然后将每部分以 base36 转换为整数
              - 若转换后的列表长度大于1，则取前两项拼接成浮点数返回，否则返回该整数
          * 其它情况：
              - 替换 value 中所有 ea 为 "~"，所有 ta 为 "!"
    """
    result = {}
    if t and isinstance(t, str):
        # 使用 "!" 分割并过滤空字符串
        for part in filter(None, t.split("!")):
            splitted = part.split("~", 1)  # 仅分割成两部分
            if len(splitted) >= 2:
                r, i = splitted[0], splitted[1]
                key = ca.get(r, r)
                # 处理 value
                if i.startswith(na):
                    if i == ia:
                        value = True
                    elif i != oa:
                        value = sa.get(i, i)
                    else:
                        value = False
                elif i.startswith(ra):
                    parts_ = i[1:].split(".")
                    try:
                        nums = [int(part, 36) for part in parts_]
                    except Exception:
                        nums = []
                    if len(nums) > 1:
                        value = float(f"{nums[0]}.{nums[1]}")
                    elif nums:
                        value = nums[0]
                    else:
                        value = i
                else:
                    value = i.replace(ea, "~").replace(ta, "!")
                result[key] = value
    return result
