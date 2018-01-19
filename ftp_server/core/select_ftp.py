# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:ZF

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from sys import path
# path.append(r'../modules')
# # from classes import *
# from classes import Feature
from lib.ftpclass import Ftpserver
import selectors
import socket
import json

sel = selectors.DefaultSelector()


def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    # conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)


def read(conn, mask):
    try:
        recv_data = conn.recv(1000)  # Should be ready
        if recv_data:
                print('echoing', repr(recv_data), 'to', conn)
                data = json.loads(recv_data.decode())
                action = data.get("action")
                obj1 = Ftpserver(conn)
                if hasattr(obj1, action):
                        func = getattr(obj1, action)
                        func(data)
                else:
                        print("task action is not supported", action)
        else:
                print('closing', conn)
                sel.unregister(conn)
                conn.close()
    except Exception as e:
        print("There is an %s error, please check the causes of error!" % e)
        sel.unregister(conn)
        conn.close()
    # finally:
    #     print('erros, closing')
    #     sel.unregister(conn)
    #     conn.close()


def run():
    sock = socket.socket()
    # sock.bind(('localhost', 9999))
    sock.bind(('0.0.0.0', 9999))
    sock.listen(100)
    sock.setblocking(False)
    sel.register(sock, selectors.EVENT_READ, accept)
    while True:
        print("start....")
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
    # print('shutting down')
    # sel.close()
