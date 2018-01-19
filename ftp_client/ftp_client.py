# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:ZF

import socket
import os
import sys
# import selectors

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import hashlib
from lib import commons


class FtpClient(object):
    BASEDIR = os.path.dirname(os.path.abspath(__file__))
    DIR = os.path.join(BASEDIR, 'Folder')
    CURRENT_DIR = ''
    Home_DIR = ''
    INFO_DIR = {}

    def __init__(self):
        self.client = socket.socket()
        pass

    def help(self):
        msg = '''
        ls 查看当前目录下文件
        cd dir (请用'cd'+'空格'+'目录')
        put filename (请用'put'+'空格'+'文件名或文件路径(test, /xx/test)'的格式上传文件)
        get filename (请用'get'+'空格'+'文件名'的格式下载文件"
        bye 退出FTP
        mkdir filename (请用'mkdir'+'空格'+'目录name')
        '''
        print(msg)

    def connect(self, ip, port):
        self.client.connect((ip, port))
        pass

    def interactive(self):
        data = self.login()
        flag = data
        FtpClient.INFO_DIR = data
        if flag:
            FtpClient.Home_DIR = FtpClient.INFO_DIR['home_dir']
            FtpClient.CURRENT_DIR = FtpClient.Home_DIR
            while True:
                cmd = input("[%s]ftp>" % FtpClient.CURRENT_DIR).strip()
                if len(cmd) == 0:
                    continue
                cmd_str = cmd.split()[0]
                if hasattr(self, "cmd_%s" % cmd_str):
                    try:
                        func = getattr(self, "cmd_%s" % cmd_str)
                        func(cmd)
                    except Exception as e:
                        print("There is an %s error, please check the causes of error!" % e)
                else:
                    self.help()
            pass
        else:
            print("登录失败！")

    def cmd_put(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            f_filename = cmd_split[1]
            # filename = os.path.basename(cmd_split[1])
            # print(FtpClient.DIR)
            # print(os.path.join(FtpClient.DIR, f_filename))
            if os.path.isfile(os.path.join(FtpClient.DIR, f_filename)):  # 判断FTPclient指定目录下是否存在将要发送的文件
                print(os.path.join(FtpClient.DIR, f_filename))
                filesize = os.stat(os.path.join(FtpClient.DIR, f_filename)).st_size
                filename = os.path.basename(f_filename)
                FtpClient.INFO_DIR['action'] = 'put'
                FtpClient.INFO_DIR['filename'] = filename
                FtpClient.INFO_DIR['size'] = filesize
                FtpClient.INFO_DIR['home_dir'] = FtpClient.Home_DIR
                FtpClient.INFO_DIR['current_dir'] = FtpClient.CURRENT_DIR
                print(FtpClient.INFO_DIR)
                self.client.send(bytes(json.dumps(FtpClient.INFO_DIR).encode("utf-8")))
                # 防止粘包，等服务器确认,可以根据服务器返回代码进行判断，比如是否有权限，磁盘配额是否大小等
                server_response = json.loads(self.client.recv(1024).decode())  # 收到服务器的回应
                if server_response['status'] == '206':  # 206表示上传的文件在服务器上已经存在，且存在的文件完整
                    msg = server_response['msg']
                    print(msg)
                    inp = input("是否继续上传覆盖文件?输入[y/n]:")
                    if inp == 'y':  # 确定覆盖
                        server_response['overridden'] = True
                        self.client.send(bytes(json.dumps(server_response).encode("utf-8")))
                        server_response2 = json.loads(self.client.recv(1024).decode())
                        if server_response2['status'] == '200':
                            f = open(os.path.join(FtpClient.DIR, f_filename), 'rb')
                            m = hashlib.md5()
                            i = 0
                            for line in f:
                                m.update(line)
                                self.client.sendall(line)
                                i += len(line)
                                j = int(i / filesize * 100)
                                symbol = '#' * j
                                spaces = ' ' * (100 - len(symbol))
                                sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                                sys.stdout.flush()
                            f.close()
                            server_response1 = self.client.recv(1024)  # 接收MD5值
                            if server_response1.decode() == m.hexdigest():  # 验证文件的MD5值是否相等
                                print("\nfile upload success")
                    elif inp == 'n':  # 不覆盖
                        pass
                elif server_response['status'] == '207':  # 207表示上传的文件在整服务器上存在，但是不完整
                    # print(server_response)
                    position = server_response['position']
                    # print(position)
                    # server_response['status'] = '200'
                    # self.client.send(bytes(json.dumps(server_response).encode("utf-8")))
                    f = open(os.path.join(FtpClient.DIR, f_filename), 'rb')
                    m = hashlib.md5()
                    i = position
                    f.seek(position)  # 定位断点的位置
                    for line in f:  # 从断点的位置开始读取数据
                        m.update(line)
                        self.client.sendall(line)
                        i += len(line)
                        j = int(i / filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        sys.stdout.flush()
                    f.close()
                    server_response1 = self.client.recv(1024)
                    if server_response1.decode() == m.hexdigest():  # 验证文件的MD5值是否相等
                        print("\nfile upload success")
                elif server_response['status'] == '208':
                    msg = server_response['msg']
                    print(msg)
                elif server_response['status'] == '200':  # 服务器准备好接受上传
                    f = open(os.path.join(FtpClient.DIR, f_filename), 'rb')
                    m = hashlib.md5()
                    i = 0
                    for line in f:
                        m.update(line)
                        self.client.sendall(line)
                        i += len(line)
                        j = int(i/filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        sys.stdout.flush()
                    f.close()
                    server_response1 = self.client.recv(1024)
                    if server_response1.decode() == m.hexdigest():
                        print("\nfile upload success")
                else:
                    print("服务器还没有准备好！")
                pass
            elif os.path.isfile(os.path.join(FtpClient.BASEDIR, f_filename)):  # ftp_client dan qian mu lu
                filesize = os.stat(os.path.join(FtpClient.BASEDIR, f_filename)).st_size
                filename = os.path.basename(f_filename)
                FtpClient.INFO_DIR['action'] = 'put'
                FtpClient.INFO_DIR['filename'] = filename
                FtpClient.INFO_DIR['size'] = filesize
                FtpClient.INFO_DIR['home_dir'] = FtpClient.Home_DIR
                FtpClient.INFO_DIR['current_dir'] = FtpClient.CURRENT_DIR
                print(FtpClient.INFO_DIR)
                self.client.send(bytes(json.dumps(FtpClient.INFO_DIR).encode("utf-8")))
                # 防止粘包，等服务器确认,可以根据服务器返回代码进行判断，比如是否有权限，磁盘配额是否大小等
                server_response = json.loads(self.client.recv(1024).decode())  # 收到服务器的回应
                if server_response['status'] == '206':  # 206表示上传的文件在服务器上已经存在，且存在的文件完整
                    msg = server_response['msg']
                    print(msg)
                    inp = input("是否继续上传覆盖文件?输入[y/n]:")
                    if inp == 'y':  # 确定覆盖
                        server_response['overridden'] = True
                        self.client.send(bytes(json.dumps(server_response).encode("utf-8")))
                        server_response2 = json.loads(self.client.recv(1024).decode())
                        if server_response2['status'] == '200':
                            f = open(os.path.join(FtpClient.BASEDIR, f_filename), 'rb')
                            m = hashlib.md5()
                            i = 0
                            for line in f:
                                m.update(line)
                                self.client.sendall(line)
                                i += len(line)
                                j = int(i / filesize * 100)
                                symbol = '#' * j
                                spaces = ' ' * (100 - len(symbol))
                                sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                                sys.stdout.flush()
                            f.close()
                            server_response1 = self.client.recv(1024)  # 接收MD5值
                            if server_response1.decode() == m.hexdigest():  # 验证文件的MD5值是否相等
                                print("\nfile upload success")
                    elif inp == 'n':  # 不覆盖
                        server_response['overridden'] = False
                        self.client.send(bytes(json.dumps(server_response).encode("utf-8")))
                        pass
                elif server_response['status'] == '207':  # 207表示上传的文件在整服务器上存在，但是不完整
                    # print(server_response)
                    position = server_response['position']
                    # print(position)
                    # server_response['status'] = '200'
                    # self.client.send(bytes(json.dumps(server_response).encode("utf-8")))
                    f = open(os.path.join(FtpClient.BASEDIR, f_filename), 'rb')
                    m = hashlib.md5()
                    i = position
                    f.seek(position)  # 定位断点的位置
                    for line in f:  # 从断点的位置开始读取数据
                        m.update(line)
                        self.client.sendall(line)
                        i += len(line)
                        j = int(i / filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        sys.stdout.flush()
                    f.close()
                    server_response1 = self.client.recv(1024)
                    if server_response1.decode() == m.hexdigest():  # 验证文件的MD5值是否相等
                        print("\nfile upload success")
                elif server_response['status'] == '208':
                    msg = server_response['msg']
                    print(msg)
                elif server_response['status'] == '200':  # 服务器准备好接受上传
                    f = open(os.path.join(FtpClient.BASEDIR, f_filename), 'rb')
                    m = hashlib.md5()
                    i = 0
                    for line in f:
                        m.update(line)
                        self.client.sendall(line)
                        i += len(line)
                        j = int(i / filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        sys.stdout.flush()
                    f.close()
                    server_response1 = self.client.recv(1024)
                    if server_response1.decode() == m.hexdigest():
                        print("\nfile upload success")
                else:
                    print("服务器还没有准备好！")
                pass
            elif os.path.isfile(f_filename):  # 判断任意目录下是否存在文件
                filesize = os.stat(f_filename).st_size
                filename = os.path.basename(f_filename)
                msg_dic = {
                    "action": "put",
                    "filename": filename,
                    "size": filesize,
                    "overridden": False,
                    "home_dir": FtpClient.Home_DIR,
                    "current_dir": FtpClient.CURRENT_DIR
                }
                self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                # 防止粘包，等服务器确认,可以根据服务器返回代码进行判断，比如是否有权限，磁盘配额是否大小等
                server_response = json.loads(self.client.recv(1024).decode())
                if server_response['status'] == '206':  # 206表示上传的文件在服务器上已经存在，且存在的文件完整
                    msg = server_response['msg']
                    print(msg)
                    inp = input("是否继续上传覆盖文件?输入[y/n]:")
                    if inp == 'y':  # 确定覆盖
                        server_response['overridden'] = True
                        self.client.send(bytes(json.dumps(server_response).encode("utf-8")))
                        server_response2 = json.loads(self.client.recv(1024).decode())
                        if server_response2['status'] == '200':
                            f = open(f_filename, 'rb')
                            m = hashlib.md5()
                            i = 0
                            for line in f:
                                m.update(line)
                                self.client.sendall(line)
                                i += len(line)
                                j = int(i / filesize * 100)
                                symbol = '#' * j
                                spaces = ' ' * (100 - len(symbol))
                                sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                                sys.stdout.flush()
                            f.close()
                            server_response1 = self.client.recv(1024)  # 接收MD5值
                            if server_response1.decode() == m.hexdigest():  # 验证文件的MD5值是否相等
                                print("\nfile upload success")
                    elif inp == 'n':  # 不覆盖
                        pass
                elif server_response['status'] == '207':  # 207表示上传的文件在整服务器上存在，但是不完整
                    # print(server_response)
                    position = server_response['position']
                    # print(position)
                    # server_response['status'] = '200'
                    # self.client.send(bytes(json.dumps(server_response).encode("utf-8")))
                    f = open(f_filename, 'rb')
                    m = hashlib.md5()
                    i = position
                    f.seek(position)  # 定位断点的位置
                    for line in f:  # 从断点的位置开始读取数据
                        m.update(line)
                        self.client.sendall(line)
                        i += len(line)
                        j = int(i / filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        sys.stdout.flush()
                    f.close()
                    server_response1 = self.client.recv(1024)
                    if server_response1.decode() == m.hexdigest():  # 验证文件的MD5值是否相等
                        print("\nfile upload success")
                elif server_response['status'] == '208':
                    msg = server_response['msg']
                    print(msg)
                if server_response['status'] == '200':
                    f = open(f_filename, 'rb')
                    m = hashlib.md5()
                    i = 0
                    for line in f:
                        m.update(line)
                        self.client.sendall(line)
                        i += len(line)
                        j = int(i/filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        sys.stdout.flush()
                    f.close()
                    server_response1 = self.client.recv(1024)
                    if server_response1.decode() == m.hexdigest():
                        print("\nfile upload success")
            else:
                print(f_filename, "is not exist")
        else:
            print("命令语法有误，请重新输入！")
        pass

    def cmd_get(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            f_filename = cmd_split[1]
            filename = os.path.basename(f_filename)
            t_filename = filename + '.tmp'  # 下载产生的不完整的临时文件
            if os.path.isfile(os.path.join(FtpClient.DIR, filename)):
                print("下载的文件已经存在！")
            elif os.path.isfile(os.path.join(FtpClient.DIR, t_filename)):  # 判断是否存在上次下载产生的临时文件，存在就进行断点续传
                filesize = os.stat(os.path.join(FtpClient.DIR, t_filename)).st_size
                print(filesize)
                msg_dic = {
                    "action": "get",
                    "filename": filename,
                    "size": '',
                    "position": filesize,
                    "overridden": None,
                    "home_dir": FtpClient.Home_DIR,
                    "current_dir": FtpClient.CURRENT_DIR,
                    "status": '199',
                }
                self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                s_response = json.loads(self.client.recv(1024).decode())
                if s_response['status'] == '200':
                    f = open(os.path.join(FtpClient.DIR, t_filename), 'ab')
                    tf_position = f.tell()
                    self.client.send(b'ok')
                    m = hashlib.md5()
                    received_size = tf_position
                    filesize = s_response['size']
                    while received_size < filesize:
                        if filesize - received_size > 1024:
                            size = 1024
                        else:
                            size = filesize - received_size
                        data = self.client.recv(size)
                        f.seek(tf_position)  # 定位断点的位置
                        f.write(data)  # 从断点的位置开始写
                        received_size += len(data)
                        j = int(received_size/filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        m.update(data)
                    else:
                        self.client.send(b'finish')
                        file_md5 = self.client.recv(1024)
                        if file_md5.decode() == m.hexdigest():
                            f.close()
                        print("\nThe file download success!")
                        # 修改下载完毕的文件名
                        os.rename(os.path.join(FtpClient.DIR, t_filename), os.path.join(FtpClient.DIR, filename))
            else:  # 全新下载文件
                msg_dic = {
                    "action": "get",
                    "filename": filename,
                    "size": None,
                    "overridden": None,
                    "home_dir": FtpClient.Home_DIR,
                    "current_dir": FtpClient.CURRENT_DIR,
                    "status": ''
                }
                self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                data = self.client.recv(1024)
                # print(data)
                cmd_dic = json.loads(data.decode())
                if cmd_dic['status'] == '200':
                    filesize = cmd_dic["size"]
                    # self.client.send(b'200')
                    f = open(os.path.join(FtpClient.DIR, f_filename + '.tmp'), 'wb')
                    self.client.send(b'ok')
                    revevied_size = 0
                    m = hashlib.md5()
                    while revevied_size < filesize:
                        if filesize - revevied_size > 1024:  # 要接收不止一次
                            size = 1024
                        else:  # 接收最后一次少于1024的数据
                            size = filesize - revevied_size
                        data = self.client.recv(size)
                        f.write(data)
                        revevied_size += len(data)
                        j = int(revevied_size/filesize * 100)
                        symbol = '#' * j
                        spaces = ' ' * (100 - len(symbol))
                        sys.stdout.write("\r[%s] %d%%" % (symbol + spaces, j))
                        m.update(data)
                    else:
                        self.client.send(b'finish')
                        file_md5 = self.client.recv(1024)
                        if file_md5.decode() == m.hexdigest():
                            f.close()
                            print("\nThe file download success!")
                            os.rename(os.path.join(FtpClient.DIR, filename + '.tmp'), os.path.join(FtpClient.DIR, filename))
                elif cmd_dic['status'] == '202':
                    msg = cmd_dic['mesg']
                    print(msg)
        else:
            print("命令语法有误，请重新输入！")
        pass

    def cmd_cd(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            msg_dic = {
                "action": "cd",
                "filename": filename,
                "home_dir": FtpClient.Home_DIR,
                "current_dir": FtpClient.CURRENT_DIR
            }
            self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
            reponse_data = json.loads(self.client.recv(1024).decode())
            if reponse_data['status'] == '402':
                print(reponse_data['mesg'])
            elif reponse_data['status'] == '400':
                print(reponse_data['current_dir'])
                print(reponse_data)
                FtpClient.CURRENT_DIR = reponse_data['current_dir']
            elif reponse_data['status'] == '401':
                print("You have to change the directory is not in your user directory")
        else:
            print("命令语法有误，请重新输入！")

    def cmd_mkdir(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) == 2:
            filename = cmd_split[1]
            tmp1 = filename.split('/')
            if len(tmp1) > 1:
                if FtpClient.Home_DIR == tmp1[1]:
                    filename = os.path.basename((cmd_split[1]))
                    msg_dic = {
                        "action": "mkdir",
                        "filename": filename,
                        "home_dir": FtpClient.Home_DIR,
                        "current_dir": FtpClient.CURRENT_DIR
                    }
                    self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                    recv_data = self.client.recv(1024)
                    if recv_data == b'99':
                        print("The directory is exists!")
                    elif recv_data == b'100':
                        print("the directory create successful!")
                elif FtpClient.Home_DIR != tmp1[1]:
                    print("you only can create directory in your home!")
            elif len(tmp1) == 1:
                    msg_dic = {
                        "action": "mkdir",
                        "filename": filename,
                        "home_dir": FtpClient.Home_DIR,
                        "current_dir": FtpClient.CURRENT_DIR
                    }
                    self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                    recv_data = self.client.recv(1024)
                    if recv_data == b'99':
                        print("The directory is exists!")
                    elif recv_data == b'100':
                        print("the directory create successful!")
        else:
            print("'mkdir'+'空格'+'目录name', create directory!")

    def cmd_ls(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) == 2:
            # filename = os.path.basename(cmd_split[1])
            filename = cmd_split[1]
            tmp1 = filename.split('/')  # 将路径进行分割
            if len(tmp1) > 1:
                if FtpClient.Home_DIR == tmp1[1]:  # 如果查看的路径父目录是否为家目录
                    filename = os.path.basename(cmd_split[1])  # 获取查看的目录
                    msg_dic = {
                        "action": "ls",
                        "filename": filename,
                        "home_dir": FtpClient.Home_DIR,
                        "current_dir": FtpClient.CURRENT_DIR
                    }
                    self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                    recv_data = json.loads(self.client.recv(1024).decode())
                    # print(recv_data)
                    if recv_data.get('res') == 0:
                        print(recv_data.get('mesg'))
                    else:
                        info_size = recv_data.get('size')
                        self.client.sendall(b'100')
                        recv_size = 0
                        data = b''
                        while recv_size < info_size:
                            data += self.client.recv(1024)
                            recv_size += len(data)
                        print(data.decode())
                else:
                    print("您要查看的目录不在家目录下，无权限查看！")
            elif len(tmp1) == 1:
                msg_dic = {
                    "action": "ls",
                    "filename": filename,
                    "home_dir": FtpClient.Home_DIR,
                    "current_dir": FtpClient.CURRENT_DIR
                }
                self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
                recv_data = json.loads(self.client.recv(1024).decode())
                # print(recv_data)
                if recv_data.get('res') == 0:
                    print(recv_data.get('mesg'))
                else:
                    info_size = recv_data.get('size')
                    self.client.sendall(b'100')
                    recv_size = 0
                    data = b''
                    while recv_size < info_size:
                        data += self.client.recv(1024)
                        recv_size += len(data)
                    print(data.decode())
        elif len(cmd_split) == 1:  # 查看当前目录下的文件
            msg_dic = {
                "action": "ls",
                "filename": '',
                "home_dir": FtpClient.Home_DIR,
                "current_dir": FtpClient.CURRENT_DIR
            }
            self.client.send(bytes(json.dumps(msg_dic).encode("utf-8")))
            recv_data = json.loads(self.client.recv(1024).decode())
            # print(recv_data)
            if recv_data.get('res') == 0:
                print(recv_data.get('mesg'))
            else:
                info_size = recv_data.get('size')
                self.client.send(b'100')
                recv_size = 0
                data = b''
                while recv_size < info_size:
                    data += self.client.recv(1024)
                    recv_size += len(data)
                print(data.decode())

    def login(self):
        name = input("username：")
        password = input("password：")
        user_dic = {
            "action": "login",
            "username": name,
            "password": commons.md5(password)
        }
        self.client.send(bytes(json.dumps(user_dic).encode("utf-8")))
        server_reponse = json.loads(self.client.recv(1024).decode())
        # print(server_reponse)
        if server_reponse['status'] == '300':
            print("登录成功！")
            return server_reponse
        elif server_reponse['status'] == '301':
            print("密码错误，登录失败！")
            return False
        elif server_reponse['status'] == '302':
            print("用户不存在！")
            return False
        pass

    @staticmethod
    def cmd_quit(*args):
        print("感谢使用FTP服务!", *args)
        exit()
        pass

    @staticmethod
    def cmd_bye(*args):
        print("感谢使用FTP服务!", *args)
        exit()


ftp = FtpClient()
# ftp.connect("localhost", 9999)
ftp.connect("192.168.8.9", 9999)
ftp.interactive()
