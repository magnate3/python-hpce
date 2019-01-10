#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
import os
import sys
import fcntl
import json
import linkstate_sockcli

PATH = 'dat/ted.json'


def update_ted(linkstate, addr):
    '''update TED'''

    if os.path.exists(PATH):
        with open(PATH, 'r') as f:
            try:
                ted = json.load(f)
            except ValueError:
                ted = {}
    else:
        ted = {}

    with open(PATH, 'w') as f:
        ted[addr[0]] = linkstate
        json.dump(ted, f)

    return


def manager(addr, linkstate, is_underpce):
    '''main of TED manager'''

    # Add linkstate to TED
    update_ted(linkstate, addr)
    print('[Link State] Update TED from {}'.format(addr[0]), file=sys.stderr)

    # if Hierarchical SR-PCE, read TED and send to upper SR-PCE
    if is_underpce:

        if os.path.exists(PATH):
            with open(PATH, 'r') as f:
                try:
                    ted = json.load(f)
                except ValueError:
                    ted = {}
        else:
            ted = {}

        linkstate = []
            for i in ted.values():
                linkstate += i

        linkstate_sockcli.lsocket(linkstate)


    return
