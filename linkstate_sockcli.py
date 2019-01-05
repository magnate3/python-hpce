#!/usr/bin/env python
# -*- coding:utf-8 -*-

import socket
import pickle


class ServAttr:
    def __init__(self):
        self.ip = ''
        self.port = 0


def lsocket(link_state):
    '''Socket of linkstate'''

    serv = ServAttr()
    serv.ip = '172.16.2.253'
    serv.port = 17932

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serv.ip, serv.port))
    s.send(pickle.dumps(link_state))
    s.close()

    return
