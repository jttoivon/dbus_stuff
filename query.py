#!/usr/bin/env python3
# Print processes which have session bus connections
# Copyright 2013 Colin Walters <walters@verbum.org>
# Licensed under the new-BSD license (http://www.opensource.org/licenses/bsd-license.php)

import sys
import argparse

#sys.path.append("/usr/lib/python3/dist-packages/")

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
parser.add_argument('-c','--command_line',  action='store_true', default=False,  help='Show the command line of the process that offers the service')
parser.add_argument('-a','--all',  action='store_true', default=False,  help='Show all services, not only well-known service')
parser.add_argument('-s','--system',  action='store_true', default=True,  help='query SystemBus (default)')
parser.add_argument('-S','--session', action='store_true', default=False, help='query SessionBus')
#parser.add_argument('-p','--pattern', help='search pattern',            required=False, default=None)
args = vars(parser.parse_args())

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#loop = gobject.MainLoop()

print(args.keys())

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

print(args["command_line"])
if args["table"]:
    tree=False
else:
    tree=True

def get_command_line(pid):
    #print("In function get_command_line")
    try:
        cmdline = os.readlink('/proc/%d/exe' % (pid, ))
    except:
        cmdline = '(unknown)'
    #print(cmdline)
    return cmdline

if not tree:
    print("Service\tObject_path\tInterface")

def rec_intro(bus, service, object_path):
    if tree:
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
        elif child.tag == "interface":
            interface = child.attrib['name']
            if tree:
                print("\t\t%s" % interface)
            else:
                print("%s\t%s\t%s" % (service, object_path, interface))
    for new_path in subobjects:
        rec_intro(bus, service, new_path)

def get_managed_object(service="org.bluez"):
    dbus_object = bus.get_object(service, "/")
    dbus_iface  = dbus.Interface(dbus_object, 'org.freedesktop.DBus.ObjectManager')
    L = dbus_iface.GetManagedObjects()
    return L

for service in connections:
    if not args["all"] and service.startswith(':'): continue
    #print(args["command_line"])
    try:
        if tree:
            print(service, end="")
            if args["pid"] or args["command_line"]:
                pid = int(driver.GetConnectionUnixProcessID(service))
            if args["pid"]:
                print("\t%i" % pid, end="")
            if args["command_line"]:
                #print("here")
                pid = int(driver.GetConnectionUnixProcessID(service))
                cmd = get_command_line(pid)
                print("\t%s" % cmd, end="")
            print()

        rec_intro(bus, service, "/")
        # ownerpid = driver.GetConnectionUnixProcessID(name)
        # pid_to_connections[ownerpid].append(name)
        # count = pid_to_count.get(ownerpid, 0)
        # pid_to_count[ownerpid] = count + 1
    except:
        continue

# for pid in sorted(pid_to_count.keys()):
#     try:
#         cmdline = os.readlink('/proc/%d/exe' % (pid, ))
#     except:
#         cmdline = '(unknown)'
#     print("%s (%d): %d connections" % (cmdline, pid, pid_to_count[pid]))

# for pid in sorted(pid_to_connections.keys()):
#     try:
#         cmdline = os.readlink('/proc/%d/exe' % (pid, ))
#     except:
#         cmdline = '(unknown)'
#     connections =  pid_to_connections[pid]
#     print("%s (%d): %d connections" % (cmdline, pid, len(connections)))
#     for c in connections:
#         print("\t%s" % c)
    
