#!/usr/bin/env python
# -*- coding:utf-8 -*-

import threading
import linkstate_socksrv
import segmentlist_socksrv
import argparse


def main(is_underpce):
    '''simple PCE for FRRouting'''

    # Receive linkstate
    thread_ls = threading.Thread(target=linkstate_socksrv.lsocket, args=(is_underpce, ))
    # Receive segment list
    thread_sl = threading.Thread(target=segmentlist_socksrv.ssocket, args=(is_underpce, ))

    thread_ls.start()
    thread_sl.start()


if __name__ == '__main__':
    # args
    parser = argparse.ArgumentParser(description='Simple SR PCE')
    parser.add_argument('-u', '--under', action='store_true',
                        help='becomes underlayer PCE of hierarchical SR PCE')
    args = parser.parse_args()

    main(args.under)
