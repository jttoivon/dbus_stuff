#!/usr/bin/env python
# Print processes which have session bus connections
# Copyright 2013 Colin Walters <walters@verbum.org>
# Licensed under the new-BSD license (http://www.opensource.org/licenses/bsd-license.php)

import sys
sys.path.append("/usr/lib/python3/dist-packages/")

import os
#import gobject
import dbus
import dbus.mainloop.glib
from collections import defaultdict
from xml.etree import ElementTree

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#loop = gobject.MainLoop()

bus = dbus.SystemBus()
#bus = dbus.SessionBus()
driver = dbus.Interface(bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus'), 'org.freedesktop.DBus')
connections = driver.ListNames()
# pid_to_count = {}
# pid_to_connections = defaultdict(list)

tree=False

def rec_intro(bus, service, object_path):
    if tree:
        print("\t%s" % object_path)
    obj = bus.get_object(service, object_path)
    iface = dbus.Interface(obj, 'org.freedesktop.DBus.Introspectable')
    xml_string = iface.Introspect()
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
    if service.startswith(':'): continue
    try:
        if tree:
            print(service)
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
    
