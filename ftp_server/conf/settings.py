# !/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:ZF

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HOST = "localhost"
PORT = 9999

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(BASEDIR, 'Folder')
Data_DIR = DIR.replace('Folder', 'db')
