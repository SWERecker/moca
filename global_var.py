_global_dict = {
    'file_list_update_time': -1
}


def _init():  # 初始化
    global _global_dict


def set_value(key, value):
    """
    定义一个全局变量

    :param key: Key
    :param value: Value
    :return:
    """
    _global_dict[key] = value


def get_value(key):
    """
    获得一个全局变量,不存在则返回默认值

    :param key: Key
    :return:
    """
    try:
        return _global_dict[key]
    except KeyError:
        return None


def value_exist(key):
    """
    查询key是否存在

    :param key: Key
    :return: True/False
    """
    return key in _global_dict
