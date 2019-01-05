#!/usr/bin/env python
# -*- coding:utf-8 -*-

import socket
import pickle
# import iproute2_apply
import time

BUFSIZE = 4096


class ServAttr:
    def __init__(self):
        self.ip = ''
        self.port = 0


def ssocket(request, is_underpce):
    '''Socket of segment list'''

    serv = ServAttr()
    serv.ip = '172.16.2.253'
    serv.port = 55384

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serv.ip, serv.port))
    # Send request (Source and Destination Address set)
    s.send(pickle.dumps(request))
    print('[Segment list] Finished sending request')
    # s.close()

    # Receive sl_info (Source and Destination, Nexthop Address, Segment list)
    sl_info = s.recv(BUFSIZE)
    print('[Segment list] Finished receiving segmentlist infomation')
    s.close()

    # if PCE
    if is_underpce:
        return pickle.loads(sl_info)
    # if PCC
    else:
        # iproute2_apply.ip_route(pickle.loads(sl_info))
        return
