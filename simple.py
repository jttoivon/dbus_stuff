#!/usr/bin/env python3

# A simple dbus program that joins either system or session bus and
# optionally register a well-known name.

import sys
import argparse

import signal # for pause
import dbus
import dbus.service

parser = argparse.ArgumentParser(description='Query dbus tree')
parser.add_argument('-p','--pid',  action='store_true', default=False,  help='Show the process id that offers the service')
parser.add_argument('-c','--command-line',  action='store_true', default=False,  help='Show the command line of the process that offers the service')
parser.add_argument('--system',  action='store_true', default=True,  help='Query SystemBus (default)')
parser.add_argument('--session', action='store_true', default=False, help='Query SessionBus')
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Print debug information')
parser.add_argument('-s','--service', help='search pattern', required=False, default=None)
args = vars(parser.parse_args())

debug = args["debug"]



if args["session"]:
    if debug:
        print("Using session bus")
    bus = dbus.SessionBus()
else:
    if debug:
        print("Using system bus")
    bus = dbus.SystemBus()

myname = bus.get_unique_name()
print("My name is %s" % myname)
if args["service"]:
    well_known_name = args["service"]
    print("Trying to register well-known name %s" % well_known_name)
    try:
        bus.request_name(well_known_name, dbus.bus.NAME_FLAG_REPLACE_EXISTING)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except dbus.exceptions.DBusException as e:
        print(e, file=sys.stderr)
        print("Add a file named %s.conf to directory %s" %(well_known_name, "/etc/dbus-1/system.d/"))
        sys.exit(1)
    print("Success!")

try:
    signal.pause()
except KeyboardInterrupt:
    print("\nService stopped")