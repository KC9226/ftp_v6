# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:ZF

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from core.main import Ftpserver
from lib.ftpclass import Ftpserver
from core.select_ftp import run
# from conf import settings

if __name__ == '__main__':
    info = '''
    1.创建FTP用户
    2.运行FTP服务
    3.退出
    '''
    flag = False
    while not flag:
        print(info)
        inp = input("请输入选择的编号：")
        if inp == '1':
            Ftpserver.create_user()
        elif inp == '2':
            run()
        elif inp == '3':
            exit()
        else:
            print("请输入编号进行操作！")

