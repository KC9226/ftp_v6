# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:ZF


# import socketserver
import json
import subprocess
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hashlib
from lib import commons
from conf import settings


class Ftpserver(object):
    USER_DICT = {}

    def __init__(self, conn):
        self.request = conn

    @staticmethod
    def create_user():
        name = input("username：").strip()
        pwd = input("password：").strip()
        pwd1 = input("Re-enter password：").strip()
        if pwd == pwd1:
            e_flag = False
            while not e_flag:
                t_quota = input("请输入磁盘配额(1-500M)：").strip()
                if 1 <= int(t_quota) <= 500:
                    disk_quota = int(t_quota) * 1024 * 1024
                    home_path = os.path.join(settings.DIR, name)
                    print(home_path)
                    if not os.path.exists(home_path):
                        os.system('mkdir' + ' ' + home_path)
                    Ftpserver.USER_DICT = Ftpserver.db_init()
                    if Ftpserver.USER_DICT is None:
                        Ftpserver.USER_DICT = {}
                    if name not in Ftpserver.USER_DICT:
                        Ftpserver.USER_DICT[name] = {
                            "action": '',
                            "username": name,
                            "password": commons.md5(pwd),
                            "quota": disk_quota,
                            "home_dir": name,
                            "current_dir": name,
                            "filename": '',
                            "size": '',
                            "position": '',
                            "overridden": False,
                            "status": ''
                        }
                        Ftpserver.db_dump(Ftpserver.USER_DICT)
                        print("用户创建成功！")
                        e_flag = True
                    else:
                        print("用户存在！")
                        e_flag = True
                else:
                    print("请输入配额范围数值！")
        else:
            print("你的密码两次输入不一致，请重新输入！")

    # def handle(self):
    #     # print(self.request, self.client_address, self.server)
    #
    #     while True:
    #         print("wait for request...")
    #         try:
    #             data = self.request.recv(1024).strip()
    #             # print("{} wrote:".format(self.client_address[0]))
    #             print(data)
    #             if len(data) == 0:
    #                 break
    #             else:
    #                 cmd_dic = json.loads(data.decode())
    #                 action = cmd_dic['action']
    #                 if hasattr(self, action):
    #                     func = getattr(self, action)
    #                     func(cmd_dic)
    #                     # self.request.send(data.upper())
    #         except ConnectionResetError as e:
    #             print("err", e)
    #             break

    def login(self, *args):
        cmd_dic = args[0]
        username = cmd_dic.get('username')
        Ftpserver.USER_DICT = Ftpserver.db_init()
        if username in Ftpserver.USER_DICT:
            if Ftpserver.USER_DICT[username]['password'] == cmd_dic.get('password'):
                print("登录成功！")
                Ftpserver.USER_DICT[username]['status'] = '300'
                print(Ftpserver.USER_DICT)
                self.request.send(bytes(json.dumps(Ftpserver.USER_DICT[username]).encode()))
                pass
            else:
                Ftpserver.USER_DICT[username]['status'] = '301'
                print("密码错误，登录失败！")
                self.request.send(bytes(json.dumps(Ftpserver.USER_DICT[username]).encode()))
        else:
            msg_dic = {"status": '302'}
            # Ftpserver.USER_DICT[username]['status'] = '302'
            # print("用户不存在！")
            # self.request.send(b'302')
            self.request.send(bytes(json.dumps(msg_dic).encode()))
            pass

    def cd(self, *args):
        cmd_dic = args[0]
        # filename = cmd_dic['filename']
        filename = cmd_dic.get('filename')
        current_dir = cmd_dic.get('current_dir')
        home_dir = cmd_dic.get('home_dir')
        if filename == '..':
            if home_dir == current_dir:
                msg = 'In the current directory for the home directory, cannot change'
                print(msg)
                cmd_dic['status'] = '402'
                cmd_dic['mesg'] = msg
                self.request.send(bytes(json.dumps(cmd_dic).encode()))
            else:
                tmp = os.path.split(current_dir)
                current_dir = tmp[0]
                cmd_dic['current_dir'] = current_dir
                cmd_dic['status'] = '400'
                self.request.send(bytes(json.dumps(cmd_dic).encode()))
            pass
        elif filename == '.':
            cmd_dic['status'] = '400'
            self.request.send(bytes(json.dumps(cmd_dic).encode()))

        elif filename.startswith('/'):
            t1 = filename.split('/')
            print(t1)
            if home_dir == t1[1]:
                c_filename = filename.strip('/')
                print(c_filename)
                f_filename = os.path.join(settings.DIR, c_filename)
                print(filename)
                print(f_filename)
                if os.path.isdir(f_filename):
                    t = cmd_dic.get('filename')
                    cmd_dic['current_dir'] = t.strip('/')
                    print(cmd_dic.get('current_dir'))
                    cmd_dic['status'] = '400'
                    self.request.send(bytes(json.dumps(cmd_dic).encode()))
                    pass
                else:
                    cmd_dic['status'] = '401'
                    print("Directory not exsits")
                    self.request.send(bytes(json.dumps(cmd_dic).encode()))
            else:
                cmd_dic['status'] = '401'
                print("You have to change the directory is not in your user directory")
                self.request.send(bytes(json.dumps(cmd_dic).encode()))
        # elif filename.startswith(home_dir):
        #     f_filename = os.path.join(settings.DIR, filename)
        #     print(filename)
        #     print(f_filename)
        #     if os.path.isdir(f_filename):
        #         cmd_dic['current_dir'] = os.path.join(current_dir, filename)
        #         print(cmd_dic.get('current_dir'))
        #         cmd_dic['status'] = '400'
        #         self.request.send(bytes(json.dumps(cmd_dic).encode()))
        #         pass
        #     else:
        #         cmd_dic['status'] = '401'
        #         print("Directory not exsits")
        #         self.request.send(bytes(json.dumps(cmd_dic).encode()))
        else:
            tmp_str = filename.strip('/')
            t_list = tmp_str.split('/')
            print(t_list)
            print(settings.DIR)
            print(home_dir)
            print(tmp_str)
            if len(t_list) == 1:
                f_filename = os.path.join(settings.DIR, home_dir, tmp_str)
                print(f_filename)
                if os.path.isdir(f_filename):
                    cmd_dic['current_dir'] = os.path.join(current_dir, filename)
                    print(cmd_dic.get('current_dir'))
                    cmd_dic['status'] = '400'
                    self.request.send(bytes(json.dumps(cmd_dic).encode()))
                    pass
                else:
                    cmd_dic['status'] = '401'
                    print("You have to change the directory is not in your user directory")
                    self.request.send(bytes(json.dumps(cmd_dic).encode()))
            elif len(t_list) > 1:
                if home_dir == t_list[0]:
                    f_filename = os.path.join(settings.DIR, tmp_str)
                    print(f_filename)
                    if os.path.isdir(f_filename):
                        cmd_dic['current_dir'] = filename
                        print(cmd_dic.get('current_dir'))
                        cmd_dic['status'] = '400'
                        self.request.send(bytes(json.dumps(cmd_dic).encode()))
                        pass
                    else:
                        cmd_dic['status'] = '401'
                        print("Directory not exsits")
                        self.request.send(bytes(json.dumps(cmd_dic).encode()))
                else:
                    msg = 'You have to change the directory is not in your user directory'
                    cmd_dic['status'] = '402'
                    cmd_dic['mesg'] = msg
                    self.request.send(bytes(json.dumps(cmd_dic).encode()))

    def ls(self, *args):
        cmd_dic = args[0]
        if 'filename' in cmd_dic:
            filename = cmd_dic.get('filename')
            current_dir = os.path.join(settings.DIR, cmd_dic.get('current_dir'), filename)
            print(current_dir)
            if os.path.isdir(current_dir):
                cmd_str = 'ls' + ' ' + current_dir
                print(filename, current_dir)
                p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE)
                res = p.stdout.read()
                if len(res) == 0:
                    send_data = 'View the directory is empty'
                    mesg_dic = {"mesg": send_data, "size": len(send_data), "res": 0}
                    self.request.send(bytes(json.dumps(mesg_dic).encode()))
                    #self.request.send(bytes(send_data.encode()))
                else:
                    msg_dic = {
                        "size": len(res),
                        "res": len(res)
                    }
                    self.request.send(bytes(json.dumps(msg_dic).encode()))
                    c_response = self.request.recv(1024)
                    if c_response == b'100':
                        # print(res)
                        send_data = str(res, encoding='utf-8')
                        print(send_data)
                        self.request.send(bytes(send_data.encode()))
            else:
                msg = "View the directory does not exist"
                print(msg)
                mesg_dic = {"mesg": msg, "size": len(msg), "res": 0}
                self.request.send(bytes(json.dumps(mesg_dic).encode()))
                #self.request.send(bytes(msg.encode()))

    def mkdir(self, *args):
        cmd_dic = args[0]
        if 'filename' in cmd_dic:
            filename = cmd_dic.get('filename')
            # t_dir = os.path.join(settings.DIR, cmd_dic.get('current_dir'))
            # new_dir = os.path.join(t_dir, filename)
            new_dir = os.path.join(settings.DIR, cmd_dic.get('current_dir'), filename)
            print(new_dir)
            if os.path.isdir(new_dir):
                self.request.send(b'99')
                print("The path is exists!")
            else:
                cmd_str = 'mkdir' + ' ' + new_dir
                p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE)
                res = p.stdout.read()
                if len(res) == 0:
                    self.request.send(b'100')
                    print("the directory create successful!")

    def put(self, *args):
        cmd_dic = args[0]
        current_dir = cmd_dic.get('current_dir')
        # home_dir = cmd_dic['home_dir']
        filename = os.path.join(settings.DIR, current_dir, cmd_dic.get('filename'))
        print(filename)
        filesize = cmd_dic.get('size')
        username = cmd_dic.get('username')
        t = Ftpserver.USER_DICT[username]['quota']
        print(t)
        user_quota = int(Ftpserver.USER_DICT[username]['quota'])
        print(user_quota)
        if os.path.isfile(filename):  # 判断上传的文件是否已经存在
            e_filesize = os.stat(filename).st_size
            print(e_filesize)
            if e_filesize == filesize:  # 判断上传的文件与已经存在的文件大小是否相等
                msg = "The file is exsit"
                msg_dic = {
                    "action": "put",
                    "filename": filename,
                    "size": filesize,
                    "position": '',
                    "overridden": False,
                    "current_dir": current_dir,
                    "msg": msg,
                    "status": '206'
                }
                self.request.send(bytes(json.dumps(msg_dic).encode('utf-8')))
                r_data = json.loads(self.request.recv(1024).decode())
                if r_data['overridden']:  # 判断是否要覆盖已经存在的文件
                    f = open(filename, 'wb')
                    r_data['status'] = '200'
                    self.request.send(bytes(json.dumps(r_data).encode('utf-8')))  # 最好也使用json格式进行返回, 可以包含状态码等信息
                    received_size = 0
                    m = hashlib.md5()
                    while received_size < filesize:
                        if filesize - received_size > 1024:
                            size = 1024
                        else:
                            size = filesize - received_size
                        data = self.request.recv(size)
                        f.write(data)
                        received_size += len(data)
                        m.update(data)
                    else:
                        self.request.send(bytes(m.hexdigest().encode()))  # 发送MD5值
                        f.close()
                        print("file recevied success")
                    pass
                else:
                    pass
            elif e_filesize < cmd_dic.get('size'):  # 判断已经存在的文件小于即将上传的文件,表示已经存在的文件不完整
                f = open(filename, 'ab')
                f_position = f.tell()
                print(f_position)
                msg_dic = {
                    "action": "put",
                    "filename": filename,
                    "size": filesize,
                    "position": f_position,
                    "overridden": False,
                    "current_dir": current_dir,
                    "msg": '',
                    "status": '207',
                    "quota": ''
                }
                self.request.send(bytes(json.dumps(msg_dic).encode('utf-8')))
                # r_data = json.loads(self.request.recv(1024))
                # f = open(filename, 'ab')
                received_size = f_position
                m = hashlib.md5()
                while received_size < filesize:
                    if filesize - received_size > 1024:
                        size = 1024
                    else:
                        size = filesize - received_size
                    data = self.request.recv(size)
                    f.seek(f_position)  # 定位断点的位置
                    f.write(data)  # 从断点的位置开始写
                    received_size += len(data)
                    m.update(data)
                else:
                    self.request.send(bytes(m.hexdigest().encode()))
                    f.close()
                    Ftpserver.USER_DICT[username]['quota'] = user_quota - received_size
                    Ftpserver.db_dump(Ftpserver.USER_DICT)
                    print("file recevied success")
                pass
        else:
            if user_quota >= filesize:  # 判断磁盘配额剩余空间大于上传文件大小
                f = open(filename, 'wb')
                # print("file not exist", filename)
                msc_dic = {"status": '200'}
                self.request.send(bytes(json.dumps(msc_dic).encode('utf-8')))  # 最好也使用json格式进行返回, 可以包含状态码等信息
                received_size = 0
                m = hashlib.md5()
                while received_size < filesize:
                    data = self.request.recv(1024)
                    f.write(data)
                    received_size += len(data)
                    m.update(data)
                else:
                    self.request.send(bytes(m.hexdigest().encode()))
                    f.close()
                    Ftpserver.USER_DICT[username]['quota'] = user_quota - received_size
                    Ftpserver.db_dump(Ftpserver.USER_DICT)
                    # file_md5 = self.request.recv(1024)
                    # if file_md5.decode() == m.hexdigest():
                    print("file recevied success")
            elif user_quota < filesize:
                msg = '''
                Disk quota remaining space %d,the quota is not enought, please contact administrator!

                ''' % user_quota
                msg_dic = {
                    "action": "put",
                    "filename": filename,
                    "size": filesize,
                    "position": '',
                    "overridden": False,
                    "current_dir": current_dir,
                    "msg": msg,
                    "status": '208',
                    "quota": user_quota
                }
                self.request.send(bytes(json.dumps(msg_dic).encode('utf-8')))

    def get(self, *args):
        cmd_dic = args[0]
        filename = cmd_dic.get('filename')
        current_dir = cmd_dic.get('current_dir')
        tmp = filename.split('/')
        # c_filesize = cmd_dic['filesize']

        if len(tmp) == 1:
            f_filename = os.path.join(settings.DIR, current_dir, filename)
        else:
            f_filename = os.path.join(settings.DIR, filename)
        print(f_filename)
        if os.path.isfile(f_filename):  # 服务器上存在文件
            filesize = os.stat(f_filename).st_size
            if cmd_dic.get('status') == '199':  # 判断是否进行断点续传
                msg_dic = {
                    "action": "get",
                    "filename": filename,
                    "size": filesize,
                    "status": '200'
                }
                self.request.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                client_response = self.request.recv(1024)
                print(client_response)
                if client_response == b'ok':
                    f = open(f_filename, 'rb')
                    f.seek(cmd_dic.get('position'))
                    m = hashlib.md5()
                    for line in f:
                        m.update(line)
                        self.request.sendall(line)
                    f.close()
                    client_response1 = self.request.recv(1024)
                    if client_response1 == b'finish':
                        self.request.send(bytes(m.hexdigest().encode('utf-8')))
                        print("file send finish!")
            else:  # 传送全部文件数据
                filesize = os.stat(f_filename).st_size
                msg_dic = {
                    "action": "get",
                    "filename": filename,
                    "size": filesize,
                    "status": '200'
                }
                self.request.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                client_response = self.request.recv(1024)
                if client_response == b'ok':
                    f = open(f_filename, 'rb')
                    m = hashlib.md5()
                    for line in f:
                        m.update(line)
                        self.request.sendall(line)
                    f.close()
                    client_response1 = self.request.recv(1024)
                    if client_response1 == b'finish':
                        self.request.send(bytes(m.hexdigest().encode('utf-8')))
                        print("file send finish!")
        else:  # 服务器上不存在文件
            msg = "file is not exist!"
            print(msg)
            msg_dic = {"status": '202', "mesg": msg}
            self.request.send(bytes(json.dumps(msg_dic).encode("utf-8")))

    @staticmethod
    def db_init():
        """
        配置文件全部读取
        :return:
        """
        if os.path.exists(os.path.join(settings.Data_DIR, 'userinfo')):
            with open(os.path.join(settings.Data_DIR, 'userinfo'), 'r') as f:
                d_dict = json.load(f)
                return d_dict

    @staticmethod
    def db_dump(d_dict):
        """
        配置文件全部写入
        :param d_dict:
        :return:
        """
        with open(os.path.join(settings.Data_DIR, 'userinfo'), 'w') as f:
            json.dump(d_dict, f)
            return True


# if __name__ == "__main__":
#     info = '''
#     1.创建FTP用户
#     2.运行FTP服务
#     '''
#     print(info)
#     inp = input("请输入选择的编号：")
#     if inp == '1':
#         Ftpserver.create_user()
#     elif inp == '2':
#         # HOST, PORT = "0.0.0.0", 9999
#         HOST, PORT = "localhost", 9999
#         # Create the server, binding to localhost on port 9999
#         # server1 = socketserver.ThreadingTCPServer((HOST, PORT), Ftpserver)
#         print("FTPserver is running")
#         # server1.serve_forever()
#     else:
#         print("请输入编号进行操作！")
