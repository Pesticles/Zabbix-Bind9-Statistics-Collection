#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'https://github.com/Pesticles/Zabbix-Bind9-Statistics-Collection'

import argparse
import json
import os
import sys
import time


JSONFILE = '/tmp/bindstats.json'
CACHELIFE = 60

parser = argparse.ArgumentParser()
parser.add_argument("action", help="discoverzones | counter | zonecounter | zonemaintenancecounter | resolvercounter "
                                   "| socketcounter | incounter | outcounter")
parser.add_argument("-z", help="zone")
parser.add_argument("-c", help="counter name")
parser.add_argument("-p", help="bind stats port")
args = parser.parse_args()

# Configurable port
port = 8653
if args.p:
    port = args.p

# Read from the cache if it exists and is less than a minute old, so we don't hit Bind directly too often.
if os.path.exists(JSONFILE) and time.time() - os.path.getmtime(JSONFILE) <= CACHELIFE:
    with open(JSONFILE) as f:
        j = json.load(f)

else:
    import http.client
    conn = http.client.HTTPConnection('localhost:{0}'.format(port))
    conn.request('GET', '/')
    resp = conn.getresponse()
    if not resp.status == 200:
        print("HTTP GET Failed")
        sys.exit(1)
    content = resp.read()
    conn.close()

    import xml.etree.ElementTree as ElementTree
    root = ElementTree.fromstring(content)

    # Build the JSON cache
    j = {
            'zones': {},
            'counter': {},
            'zonemaintenancecounter': {},
            'resolvercounter': {},
            'socketcounter': {},
            'incounter': {},
            'outcounter': {},
            }
    for view in root.iterfind('./bind/statistics/views/view'):
        if view.findtext('./name') in ('_default',):
            for zone in view.iterfind('./zones/zone'):
                if zone.find('./counters') is not None:
                    counters = {}
                    for counter in zone.iterfind('./counters/*'):
                        counters[counter.tag] = counter.text
                    j['zones'][zone.findtext('./name')] = counters
    for stat in root.iterfind('./bind/statistics/server/nsstat'):
        j['counter'][stat.findtext('./name')] = stat.findtext('./counter')
    for stat in root.iterfind('./bind/statistics/server/zonestat'):
        j['zonemaintenancecounter'][stat.findtext('./name')] = stat.findtext('./counter')
    for view in root.iterfind('./bind/statistics/views/view'):
        if view.findtext('./name') in ('_default',):
            for stat in view.iterfind('./resstat'):
                j['resolvercounter'][stat.findtext('./name')] = stat.findtext('./counter')
    for stat in root.iterfind('./bind/statistics/server/sockstat'):
        j['socketcounter'][stat.findtext('./name')] = stat.findtext('./counter')
    for stat in root.iterfind('./bind/statistics/server/queries-in/rdtype'):
        j['incounter'][stat.findtext('./name')] = stat.findtext('./counter')
    for stat in root.iterfind('./bind/statistics/views/view/rdtype'):
        j['outcounter'][stat.findtext('./name')] = stat.findtext('./counter')

    with open(JSONFILE, 'w') as f:
        json.dump(j, f)

if args.action == 'discoverzones':
    d = {'data': [{'{#ZONE}': zone} for zone in j['zones'].keys()]}
    print(json.dumps(d))
    sys.exit(0)

elif args.action == 'zonecounter':
    if not (args.z and args.c):
        print("Missing argument", file=sys.stderr)
        print("ZBX_NOTSUPPORTED")
        sys.exit(1)
    if args.z in j['zones'] and args.c in j['zones'][args.z]:
        print(j['zones'][args.z][args.c])
        sys.exit(0)
    else:
        print("ZBX_NOTSUPPORTED")
        sys.exit(1)

else:
    if not args.c:
        print("Missing argument", file=sys.stderr)
        print("ZBX_NOTSUPPORTED")
        sys.exit(1)
    if args.c in j[args.action]:
        print(j[args.action][args.c])
        sys.exit(0)
    else:
        print("ZBX_NOTSUPPORTED")
        sys.exit(1)
