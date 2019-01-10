#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import math
from collections import defaultdict
from heapq import *


def construct_lsalist(linkstate):
    '''construct LSA list'''

    lsalist = {}

    for i in range(len(linkstate)):
        if linkstate[i].get('Opaque-Type') == 4:
            # Get SRGB
            if not linkstate[i].get('Advertising Router') in lsalist:
                lsalist[linkstate[i].get('Advertising Router')] = [0, {}]
            lsalist[linkstate[i].get('Advertising Router')][0] \
                += linkstate[i].get('Segment Routing Range TLV')[1].get('SID Label')

        elif linkstate[i].get('Opaque-Type') == 7:
            # Get Node SID (Index)
            if not linkstate[i].get('Advertising Router') in lsalist:
                lsalist[linkstate[i].get('Advertising Router')] = [0, {}]
            lsalist[linkstate[i].get('Advertising Router')][0] \
                += linkstate[i].get('Prefix SID Sub-TLV')[4].get('Index')

        elif linkstate[i].get('Opaque-Type') == 8:
            # Get Adjacency SID
            if not linkstate[i].get('Advertising Router') in lsalist:
                lsalist[linkstate[i].get('Advertising Router')] = [0, {}]
            if not linkstate[i].get('Extended Link TLV')[2].get('Link ID') in lsalist[linkstate[i].get('Advertising Router')][1]:
                lsalist[linkstate[i].get('Advertising Router')][1][linkstate[i].get(
                    'Extended Link TLV')[2].get('Link ID')] = [0, 0, 0]

            lsalist[linkstate[i].get('Advertising Router')][1][linkstate[i].get('Extended Link TLV')[2].get('Link ID')][0]\
                = linkstate[i].get('Extended Link TLV')[3].get('Link data')

            if linkstate[i].get('Adj-SID Sub-TLV') is not None:
                lsalist[linkstate[i].get('Advertising Router')][1][linkstate[i].get('Extended Link TLV')[2].get('Link ID')][1]\
                    = linkstate[i].get('Adj-SID Sub-TLV')[4].get('Label')
            else:
                lsalist[linkstate[i].get('Advertising Router')][1][linkstate[i].get('Extended Link TLV')[2].get('Link ID')][1]\
                    = linkstate[i].get('LAN-Adj-SID Sub-TLV')[5].get('Label')
            if linkstate[i].get('Inter SR Subdomain') == 'True':
                lsalist[linkstate[i].get('Advertising Router')][1][linkstate[i].get(
                    'Extended Link TLV')[2].get('Link ID')].append('intersubdomain')

    for i in range(len(linkstate)):
        if linkstate[i].get('Opaque-Type') == 1:
            # Get link information(ID, Bandwidth)
            for j in lsalist[linkstate[i].get('Advertising Router')][1].values():
                if linkstate[i].get('Local Interface IP Addresses')[0].get('0') == [j][0][0]:
                    [j][0][2] = linkstate[i].get(
                        'Maximum Reservable Bandwidth')

    return lsalist


def construct_graph(lsalist):
    '''construct graph from linkstate'''

    graph = []
    list_keys = []

    for i in lsalist.keys():
        list_keys.append(i)

    for i in range(len(list_keys)):
        for j in range(i + 1, len(list_keys)):
            for k in lsalist[list_keys[i]][1]:
                if k in lsalist[list_keys[j]][1]:
                    intersubdomain = False
                    if 'intersubdomain' in lsalist[list_keys[i]][1].get(k):
                        intersubdomain = True
                    graph.append([list_keys[i], list_keys[j],
                                  lsalist[list_keys[i]][1].get(k)[2], k, intersubdomain])

    print(graph)
    return graph


def with_info_graph(graph):
    for i in range(len(graph)):
        graph[i].insert(2, math.ceil(1000000 / graph[i][2]))
    return graph


def cspf_dijkstra(src, dst, graph, policy):
    '''CSPF (constrained dijkstra algorithm)'''

    directed_graph = defaultdict(list)

    # create directed graph
    for i in range(len(graph)):
        # BW constrain and avoid node
        if graph[i][3] >= policy['bandwidth'] and set([graph[i][0], graph[i][1]]) & set(policy['avoid_nodes']) == set():
            directed_graph[graph[i][0]].append((graph[i][2], graph[i][1]))
            directed_graph[graph[i][1]].append((graph[i][2], graph[i][0]))

    # queue, closedlist
    q, seen = [(0, src, ())], set()
    while q:
        (cost, v1, path) = heappop(q)
        if v1 not in seen:
            seen.add(v1)
            path = (v1, path)
            # clean output
            if v1 == dst:
                stack = []
                while len(path) > 1:
                    stack.insert(0, path[0])
                    path = path[1]
                return (stack)

            for c, v2 in directed_graph.get(v1, ()):
                if v2 in seen:
                    continue
                next = cost + c
                heappush(q, (next, v2, path))
    # if unreachable
    return 'inf'


def dijkstra(src, dst, graph):
    '''general dijkstra algorithm'''
    directed_graph = defaultdict(list)
    # create directed graph
    for i in range(len(graph)):
        directed_graph[graph[i][0]].append((graph[i][2], graph[i][1]))
        directed_graph[graph[i][1]].append((graph[i][2], graph[i][0]))

    # queue, closedlist
    q, seen = [(0, src, ())], set()
    while q:
        (cost, v1, path) = heappop(q)
        if v1 not in seen:
            seen.add(v1)
            path = (v1, path)
            # clean output to stack
            if v1 == dst:
                stack = []
                while len(path) > 1:
                    stack.insert(0, path[0])
                    path = path[1]
                return (stack)

            for c, v2 in directed_graph.get(v1, ()):
                if v2 in seen:
                    continue
                next = cost + c
                heappush(q, (next, v2, path))
    # if unreachable
    return 'inf'


def retour(src, dst, info_graph, constrained_path, lsalist):

    retour_list = []

    for i in range(1, len(constrained_path)):
        # 宛先よりiノード前までが最短経路かを調べる
        if constrained_path[:-i] == dijkstra(src, constrained_path[-(i+1)], info_graph):
            # 最短が見つかったらそのNode SIDをappend
            retour_list.append(lsalist[constrained_path[-(i+1)]][0])
            # 中間ノードから先が最短経路と一致しないなら
            if constrained_path[-(i+1):] != dijkstra(constrained_path[-(i+1)], dst, info_graph):
                # 中間ノードをsrcに変えてもう一度検索
                retour_list.append(retour(
                    constrained_path[-(i+1)], dst, info_graph. constrained_path[-(i+1):], lsalist))

            else:
                # dstまでが最短経路なら宛先のNode SIDを加えて終了
                retour_list.append(lsalist[constrained_path[-1]][0])
                return retour_list

    # 一個前でも最短経路でないならば，そこへのAdj SIDをsegmentlistにappend
    retour_list.append(lsalist[src][1][constrained_path[1]])
    # 隣接ノードがdstでないならば
    if constrained_path[1] != dst:
        # 一つ先からもう一度検索
        retour_list.append(
            retour(constrained_path[i], dst, info_graph. constrained_path[1:], lsalist))

    return retour_list


def check_interdomain(node_a, node_b, info_graph):

    isinterdomain = False

    print('Start check: {}, {}'.format(node_a, node_b))
    for i in info_graph:
        if node_a in i and node_b in i:
            if i[5] == True:
                isinterdomain = True

    return isinterdomain

def create_segmentlist(src, dst, info_graph, lsalist, constrained_path):
    '''convert CSPF path to segmentlist'''

    segmentlist = []

    # 前からサーチ，制約付き最短経路にサブドメイン超えが含まれていた場合
    for i in range(len(constrained_path)-1):
        if check_interdomain(constrained_path[i], constrained_path[i+1], info_graph):
            # それ以前とそれ以降に分割し処理
            shortest_path = dijkstra(src, constrained_path[i], info_graph)

            # 制約付き最短経路が最短経路と異なる場合はNode SIDで直接指定不可
            if constrained_path[:i+1] != shortest_path:
                # 迂回路のセグメントリストを構築し追記
                segmentlist += retour(src, constrained_path[i], info_graph, constrained_path[:i], lsalist)
            else:
                # 直接Node SIDを追加
                segmentlist.append(lsalist[constrained_path[i]][0])

            # サブドメイン越えのAdj SIDを付加
            # segmentlist.append(lsalist[constrained_path[i]][2][constrained_path[i+1]])
            for j in info_graph:
                if (constrained_path[i] == j[0] or constrained_path[i+1] == j[0]) and (constrained_path[i] == j[1] or constrained_path[i+1] == j[1]):
                    segmentlist.append(lsalist[constrained_path[i]][1][j[4]][1])

            # それ以降があれば
            if constrained_path[i+1] != dst:
                # 以降をまたサブドメイン越えが無いか処理，セグメントリストに追加
                segmentlist += create_segmentlist(constrained_path[i+1], dst, info_graph, lsalist, constrained_path[i+1:])

            return segmentlist

    # サブドメイン越えがなかった場合
    shortest_path = dijkstra(src, dst, info_graph)

    # 制約付き最短経路が最短経路と異なる場合はNode SIDで直接指定不可
    if constrained_path != shortest_path:
        # 迂回路のセグメントリストを構築し追記
        segmentlist += retour(src, dst, info_graph, constrained_path, lsalist)
    else:
        # 直接Node SIDを追加
        segmentlist.append(lsalist[dst][0])

    return segmentlist


def path_verification(src, via, info_graph, policy, lsalist):
    '''Verify path'''

    segmentlist = []
    via.insert(0, src)

    # パスを経由ごとに分解し経路計算
    for i in range(len(via)-1):
        # 経由地までの制約付きパスを計算
        constrained_path = cspf_dijkstra(via[i], via[i+1], info_graph, policy)

        # 到達不能の処理
        if constrained_path == 'inf':
            return None, 'Unreachable'

        # srcのnext hopを記録
        if i == 0:
            for j in lsalist[constrained_path[1]][1].values():
                if j[0] in lsalist[constrained_path[0]][1]:
                    nexthop = j[0]

        # 経由地までのセグメントリストを構築
        segmentlist += create_segmentlist(via[i], via[i+1], info_graph, lsalist, constrained_path)


    # if head is nexthop's Node SID, remove it.
    for i in info_graph:
        if i[0] == src:
            if segmentlist[0] == lsalist[i[1]][0]:
                segmentlist.pop(0)
                break

        elif i[1] == src:
            if segmentlist[0] == lsalist[i[0]][0]:
                segmentlist.pop(0)
                break

    # convert segmentlist format [16000, 16001] to '16000/16001'
    segmentlist_stack = ''
    for i in range(len(segmentlist)):
        segmentlist_stack += str(segmentlist[i])
        if i != len(segmentlist)-1:
            segmentlist_stack += '/'

    if segmentlist_stack == '':
        segmentlist_stack = 'Unreachable'

    return nexthop, segmentlist_stack


def create_sl(src, dst, via, policy, linkstate):
    '''create segmentlist'''

    # Linkstate list from TED
    lsalist = construct_lsalist(linkstate)
    # Make graph for Dijkstra [nodeA, nodeB, cost, ...]
    graph = construct_graph(lsalist)
    # Add information in graph
    info_graph = with_info_graph(graph)
    # Make segmentlist
    nexthop, segmentlist_stack = path_verification(
        src, via, info_graph, policy, lsalist)

#     print('Router Info: {}\n'.format(lsalist))
    print('Topology: {}'.format(graph))
    print('Policy:')
    print('\tQoS (Minimum BandWidth): {}'.format(policy['bandwidth']))
    print('\tAvoid Node: {}'.format(policy['avoid_nodes']))
    print('Src: {}'.format(src))
    print('Dst: {}'.format(dst))
    print('Via: {}\n'.format(via))
    print('-> Next Hop P2P Addr: {}'.format(nexthop))
    print('   Segment List: {}'.format(segmentlist_stack))

    sl_info = {'src': src, 'dst': dst, 'nexthop': nexthop,
               'segmentlist': segmentlist_stack}
    return (sl_info)
