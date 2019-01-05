#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
import os
import sys
import json
import linkstate_sockcli

PATH = 'dat/ted.json'


def check_ted(linkstate, addr):
    '''check TED'''

    if os.path.exists(PATH):
        with open(PATH, 'r') as f:
            ted = json.load(f)

        if linkstate == ted[addr[0]]:
            return 0

    return -1


def update_ted(linkstate, addr):
    '''update TED'''

    with open(PATH, 'w') as f:
        json.dump({addr[0]: linkstate}, f)

    return


def manager(addr, linkstate, is_underpce):
    '''main of TED manager'''

    # fork (Hierarchical SR-PCE)
    if is_underpce:
        pid = os.fork()
        if pid == 0:
            # Child process: Call linkstate_sockcli (Send linkstate to Upper PCE)
            linkstate_sockcli.lsocket(linkstate)

        elif pid > 0:
            # Parent process: Recode linkstate to TED
            ret = check_ted(linkstate, addr)
            # TED entry is not exist
            if ret != 0:
                # Add linkstate to TED
                update_ted(linkstate, addr)
                print('[Link State] Update TED information from {}'.format(
                    addr[0]), file=sys.stderr)
            # Wait child process
            os.wait()
        else:
            # fork error
            print('[Link State] fork failed'.format(addr[0]), file=sys.stderr)

    # General PCE
    else:
        ret = check_ted(linkstate, addr)
        # TED entry is not exist
        if ret != 0:
            # Add linkstate to TED
            update_ted(linkstate, addr)
            print('[Link State] Update TED information from {}'.format(
                addr[0]), file=sys.stderr)

    return
