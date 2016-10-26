#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'https://github.com/Pesticles/Zabbix-Bind9-Statistics-Collection'

import argparse
import json
import os
import sys
import time
import re


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
    # first, we need to see what statistics version we are. 2.x or 3.x
    # if root tag is isc = we have probably stats version 2, if it stats with statisics we have version 3 or newer
    if root.tag == 'isc':
        # get statistics version from isc/bind/statistics attrib
        version = root.find('./bind/statistics').attrib['version']
    elif root.tag == 'statistics':
        version = root.attrib['version']
    else:
        print("Unknown root tag: {}".format(root.ag), file=sys.stderr)
        print("ZBX_NOTSUPPORTED")
    # check the statistics version here
    v = re.match('^(\d{1})\.', version)
    version = int(v.group(1))
    if version < 0 or version > 3:
        print("Unsupported bind statistics version: {}".format(root.attrib), file=sys.stderr)
        print("ZBX_NOTSUPPORTED")

    # Build the JSON cache
    j = {
            'zones': {},
            'counter': {},
            'zonemaintenancecounter': {},
            'resolvercounter': {},
            'socketcounter': {},
            'incounter': {},
            'outcounter': {},
            'cache': {},
            'memory': {}
        }
    # this is for version 2
    if version == 2:
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
        # Memory
        for child in root.iterfind('./bind/statistics/memory/summary/*'):
            j['memory'][child.tag] = child.text
        # Cache for local
        for child in root.iterfind('./bind/statistics/views/view/cache'):
            if child.attrib['name'] == 'localhost_resolver':
                for stat in child.iterfind('./rrset'):
                    j['cache'][stat.findtext('./name')] = stat.findtext('./counter')

    # this is for newer version 3
    if version == 3:
        for child in root.iterfind('./server/counters'):
            # V2 ./bind/statistics/server/nsstat
            if child.attrib['type'] == 'nsstat':
                for stat in child.iterfind('./counter'):
                    j['counter'][stat.attrib['name']] = stat.text
            # V2 ./bind/statistics/server/sockstat
            if child.attrib['type'] == 'sockstat':
                for stat in child.iterfind('./counter'):
                    j['socketcounter'][stat.attrib['name']] = stat.text
            # V2 ./bind/statistics/server/zonestat
            if child.attrib['type'] == 'zonestat':
                for stat in child.iterfind('./counter'):
                    j['zonemaintenancecounter'][stat.attrib['name']] = stat.text
            # V2 ./bind/statistics/server/queries-in/rdtype
            if child.attrib['type'] == 'qtype':
                for stat in child.iterfind('./counter'):
                    j['incounter'][stat.attrib['name']] = stat.text
        # they are only for block _default
        for child in root.iterfind('./views/view/counters'):
            # V2 ./bind/statistics/views/view/rdtype
            if child.attrib['type'] == 'resqtype':
                for stat in child.iterfind('./counter'):
                    j['outcounter'][stat.attrib['name']] = stat.text
            # V2 ./bind/statistics/views/view => _default name only
            if child.attrib['type'] == 'resstats':
                for stat in child.iterfind('./counter'):
                    j['resolvercounter'][stat.attrib['name']] = stat.text
            # V2: no (only in memory detail stats)
            if child.attrib['type'] == 'cachestats':
                for stat in child.iterfind('./counter'):
                    j['cache'][stat.attrib['name']] = stat.text
        # V2 has @name = localhost_resolver, interal, external
        for child in root.iterfind('./views/view/cache'):
            if (child.attrib['name'] == '_default'):
                for stat in child.iterfind('./rrset'):
                    j['cache'][stat.findtext('./name')] = stat.findtext('./counter')
                    # for sets stating with !, we replace that with an _ (! is not allowed in zabbix)
                    if re.match('^!', stat.findtext('./name')):
                        j['cache'][stat.findtext('./name').replace('!', '_')] = stat.findtext('./counter')
        # for all the Zone stats only
        for child in root.iterfind('./views/view'):
            # only for default
            if (child.attrib['name'] == '_default'):
                # V2 ./bind/statistics/views/view -> ./zones/zone => _default name only
                for zone in child.iterfind('./zones/zone'):
                    counters = {}
                    for stat in zone.iterfind('./counters'):
                        if stat.attrib['type'] == 'rcode' or stat.attrib['type'] == 'qtype':
                            for counter in stat.iterfind('./counter'):
                                counters[counter.attrib['name']] = counter.text
                    j['zones'][zone.attrib['name']] = counters
        # V2 ./bind/statistics/memory/summary/*
        for child in root.iterfind('./memory/summary/*'):
            j['memory'][child.tag] = child.text

    # write to cache is the same in both version
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
