#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:ZF

# import os
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hashlib


def md5(arg):
    """
    md5加密
    :param arg:
    :return:
    """
    obj = hashlib.md5()
    obj.update(bytes(arg, encoding='utf-8'))
    return obj.hexdigest()



# print(md5("123"))