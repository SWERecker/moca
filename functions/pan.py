from function import ucf


def pan_change(qq: int, amount: int) -> list:
    """
    面包数量变化.

    :param qq: 用户QQ
    :param amount: 变化的数量(以正负区别增加、消耗)
    :return: [成功/失败(True/False), 变化后的数量，失败返回-1]
    """
    if amount > 0:
        res = ucf.update_one({"qq": qq}, {"$inc": {"pan": amount}})
        if res.modified_count == 0:
            ucf.insert_one({"qq": qq, "pan": amount})
            return [True, amount]
        else:
            new_pan_amount = ucf.find_one({"qq": qq}, {"pan": 1})
            return [True, new_pan_amount['pan']]
    else:
        user_data = ucf.find_one({"qq": qq}, {"_id": 0, "pan": 1})
        try:
            original_pan_amount = user_data['pan']
            if original_pan_amount + amount < 0:
                return [False, -1]
            else:
                ucf.update_one({"qq": qq}, {"$inc": {"pan": amount}})
                new_pan_amount = ucf.find_one({"qq": qq}, {"pan": 1})['pan']
                return [True, new_pan_amount]
        except TypeError:
            return [False, -1]
        except KeyError:
            return [False, -1]
