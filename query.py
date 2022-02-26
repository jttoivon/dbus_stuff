#!/usr/bin/env python3

# Print services, objects and interfaces available in eith system or session dbus.

# Copyright 2013 Colin Walters <walters@verbum.org>
# Licensed under the new-BSD license (http://www.opensource.org/licenses/bsd-license.php)

# Ideas from the following page were used:
# https://unix.stackexchange.com/questions/203410/how-to-list-all-object-paths-under-a-dbus-service

import sys
import argparse
import fnmatch

import os
#import gobject
import dbus
import dbus.mainloop.glib
from collections import defaultdict
from xml.etree import ElementTree

parser = argparse.ArgumentParser(description='query dbus tree')
#parser.add_argument('-s','--system',  nargs='?', help='query SystemBus (default)', required=False, default=True)
#parser.add_argument('-S','--session', nargs='?', help='query SessionBus',          required=False, default=False)
parser.add_argument('-t','--table',  action='store_true', default=False,  help='Show results as a table instead of a tree')
parser.add_argument('-p','--pid',  action='store_true', default=False,  help='Show the process id that offers the service')
parser.add_argument('-c','--command-line',  action='store_true', default=False,  help='Show the command line of the process that offers the service')
parser.add_argument('-a','--all',  action='store_true', default=False,  help='Show all services, not only well-known service')
parser.add_argument('--system',  action='store_true', default=True,  help='query SystemBus (default)')
parser.add_argument('--session', action='store_true', default=False, help='query SessionBus')
parser.add_argument('-s','--service', help='search pattern', required=False, default="*")
parser.add_argument('-o','--object-path', help='search pattern', required=False, default=None)
parser.add_argument('-i','--interface', help='search pattern', required=False, default=None)
args = vars(parser.parse_args())

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#loop = gobject.MainLoop()

#print(args.keys())

if args["session"]:
    #print("Using session bus")
    bus = dbus.SessionBus()
else:
    #print("Using system bus")
    bus = dbus.SystemBus()

#sys.exit(1)
driver = dbus.Interface(bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus'), 'org.freedesktop.DBus')
connections = driver.ListNames()
# pid_to_count = {}
# pid_to_connections = defaultdict(list)

#print(args["command_line"])
if args["table"]:
    tree=False
else:
    tree=True

depth = 1
if args["object_path"]:
    depth = 2
if args["interface"]:
    depth = 3
    if not args["object_path"]:
        args["object_path"] = "*"
print("Depth is %i" % depth)
print("Service pattern is %s" % args["service"])
if args["object_path"]:
    print("Object path pattern is %s" % args["object_path"])
if args["interface"]:
    print("Interface pattern is %s" % args["interface"])
def get_command_line(pid):
    #print("In function get_command_line")
    try:
        #cmdline = os.readlink('/proc/%d/exe' % (pid, ))
        with open("/proc/%d/cmdline" % (pid, )) as f:
            cmdline = f.readline().replace("\0", " ")
    except:
        cmdline = '(unknown)'
    #print(cmdline)
    return cmdline

columns = ["Service"]
if depth >= 2:
    columns.append("Object_path")
if depth >= 3:
    columns.append("Interface")
if "pid" in args:
    columns.append("Pid")
if "command_line" in args:
    columns.append("Command")
if not tree:
    print("\t".join(columns))

def rec_intro(bus, service, object_path, cursor):
    #print("In rec_intro")
    skip_object = not fnmatch.fnmatch(object_path, args["object_path"])
    if skip_object:
        print("Skipping object %s" % object_path)
    if tree and not skip_object:
        print("\t%s" % object_path)
    obj = bus.get_object(service, object_path)
    iface = dbus.Interface(obj, 'org.freedesktop.DBus.Introspectable')
    try:
        xml_string = iface.Introspect()
    except DBusException:   # No root object or no Introspectable interface
        return
    subobjects = []
    for child in ElementTree.fromstring(xml_string):
        if child.tag == 'node':
            if object_path == '/':
                object_path = ''
            new_path = '/'.join((object_path, child.attrib['name']))
            subobjects.append(new_path)
        elif child.tag == "interface" and not skip_object:
            interface = child.attrib['name']
            skip_interface = args["interface"] and not fnmatch.fnmatch(interface, args["interface"])
            if tree:
                if depth == 3 and not skip_interface:
                    print("\t\t%s" % interface)
            else:
                print("%s\t%s" % (service, object_path), end="")
                if depth == 3 and not skip_interface:
                    print("\t%s" % interface, end="")
                if args["pid"]:
                    print("\t%s" % cursor["pid"], end="")
                if args["command_line"]:
                    print("\t%s" % cursor["command_line"], end="")
                print()
    for new_path in subobjects:
        rec_intro(bus, service, new_path, cursor)

def get_managed_object(service="org.bluez"):
    dbus_object = bus.get_object(service, "/")
    dbus_iface  = dbus.Interface(dbus_object, 'org.freedesktop.DBus.ObjectManager')
    L = dbus_iface.GetManagedObjects()
    return L

for service in connections:
    if not args["all"] and service.startswith(':'): continue
    if not fnmatch.fnmatch(service, args["service"]):
        continue
    #print(args["command_line"])
    try:
        cursor = {"service" : service}
        if args["pid"] or args["command_line"]:
            cursor["pid"] = int(driver.GetConnectionUnixProcessID(service))
        if args["command_line"]:
            #print("here")
            cursor["command_line"] = get_command_line(cursor["pid"])
        if tree:
            print(service, end="")
            if args["pid"]:
                print("\t%i" % cursor["pid"], end="")
            if args["command_line"]:
                print("\t%s" % cursor["command_line"], end="")
            print()
            if depth > 1:
                rec_intro(bus, service, "/", cursor)
        else:
            if depth > 1:
                rec_intro(bus, service, "/", cursor)
            else:
                print(service, end="")
                if args["pid"]:
                    print("\t%i" % cursor["pid"], end="")
                if args["command_line"]:
                    print("\t%s" % cursor["command_line"], end="")
                print()

        # ownerpid = driver.GetConnectionUnixProcessID(name)
        # pid_to_connections[ownerpid].append(name)
        # count = pid_to_count.get(ownerpid, 0)
        # pid_to_count[ownerpid] = count + 1
    except:
        continue

