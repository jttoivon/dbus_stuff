#!/usr/bin/env python3

# Print services, objects and interfaces available in eith system or session dbus.

# Copyright 2013 Colin Walters <walters@verbum.org>
# Licensed under the new-BSD license (http://www.opensource.org/licenses/bsd-license.php)

# Ideas from the following page were used:
# https://unix.stackexchange.com/questions/203410/how-to-list-all-object-paths-under-a-dbus-service


# Note in the program the variable depth doesn't refer to the depth of the objects hierarchy.
# Instead the meaning is the following
# depth==1 is the service level
# depth==2 is the object path level
# depth==3 is the interface level

import sys
import argparse
import fnmatch

import os
#import gobject
import dbus
import dbus.mainloop.glib
from collections import defaultdict
from xml.etree import ElementTree

parser = argparse.ArgumentParser(description='Query dbus tree')
parser.add_argument('-t','--table',  action='store_true', default=False,  help='Show results as a table instead of a tree')
parser.add_argument('-p','--pid',  action='store_true', default=False,  help='Show the process id that offers the service')
parser.add_argument('-c','--command-line',  action='store_true', default=False,  help='Show the command line of the process that offers the service')
parser.add_argument('-a','--all',  action='store_true', default=False,  help='Show all services, not only well-known service')
parser.add_argument('--system',  action='store_true', default=True,  help='Query SystemBus (default)')
parser.add_argument('--session', action='store_true', default=False, help='Query SessionBus')
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Print debug information')
parser.add_argument('-s','--service', help='search pattern', required=False, default="*")
parser.add_argument('-o','--object-path', help='search pattern', required=False, default=None)
parser.add_argument('-i','--interface', help='search pattern', required=False, default=None)
parser.add_argument('--timeout', help='Timeout in seconds', required=False, default=None)
args = vars(parser.parse_args())

debug = args["debug"]

if args["timeout"]:
    timeout = float(args["timeout"])
else:
    timeout=2

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#loop = gobject.MainLoop()

#print(args.keys())

if args["session"]:
    #print("Using session bus")
    bus = dbus.SessionBus()
else:
    #print("Using system bus")
    bus = dbus.SystemBus()

myname = bus.get_unique_name()
if debug:
    print("My name is %s" % myname) 
#sys.exit(1)
driver = dbus.Interface(bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus'), 'org.freedesktop.DBus')
connections = driver.ListNames()
# pid_to_count = {}
# pid_to_connections = defaultdict(list)

if debug:
    print("Got the following command line args: %s" % args["command_line"])
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

if debug:
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
            cmdline = f.readline().replace("\0", " ").strip()
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

def print_service_pid_command(cursor, sep=" "):
    print(cursor["service"], end="")
    if args["pid"]:
        print("%s%i" % (sep, cursor["pid"]), end="")
    if args["command_line"]:
        print("%s%s" % (sep, cursor["command_line"]), end="")
    print()

def print_pid_command(cursor, sep=" "):
    if args["pid"] or args["command_line"]:
        L = []
        if args["pid"]:
            L.append("%i" % (cursor["pid"]))
        if args["command_line"]:
            L.append("'%s'" % (cursor["command_line"]))
        return " (%s)" % sep.join(L)
    else:
        return ""

def rec_intro(bus, service, object_path, cursor, service_printed=False):
    object_printed = False
    #print("In rec_intro")
    skip_object = not fnmatch.fnmatch(object_path, args["object_path"])
    #if skip_object:
    #    print("Skipping object %s" % object_path)
    if tree and not skip_object and depth == 2:
        if not service_printed:
            print_service_pid_command(cursor)
            service_printed=True
        print("\t%s" % object_path)
    obj = bus.get_object(service, object_path)
    iface = dbus.Interface(obj, 'org.freedesktop.DBus.Introspectable')
    try:
        #xml_string = iface.Introspect()
        # The above line has timeout of 25+25 seconds. The below call allows us to set
        # the timeout ourselves.
        xml_string = bus.call_blocking(service, object_path, 'org.freedesktop.DBus.Introspectable', "Introspect", 
            "", [], timeout=timeout, byte_arrays=False)
    except dbus.exceptions.DBusException as e:   # No root object or no Introspectable interface
        #print("Got an exception when trying introspection")
        #print(type(e))
        #print(e)
        name = e.get_dbus_name()
        if name == "org.freedesktop.DBus.Error.UnknownObject":
            print("The service %s%s has no root object" % (service, print_pid_command(cursor)), file=sys.stderr)
        elif name == "org.freedesktop.DBus.Error.NoReply":
            print("The service %s%s did not reply to introspection within time of %.2f seconds" % (service, print_pid_command(cursor), timeout), file=sys.stderr)
        else:
            print("Message %s" % e.get_dbus_message(), file=sys.stderr)
            print("Name %s" % name, file=sys.stderr)
        return
    subobjects = []
    # Iterate over interfaces and subobjects
    for child in ElementTree.fromstring(xml_string):
        if child.tag == 'node':   # Found a new subobject. Add it to the list
            if object_path == '/':
                object_path = ''
            new_path = '/'.join((object_path, child.attrib['name']))
            subobjects.append(new_path)
        elif child.tag == "interface" and not skip_object:
            interface = child.attrib['name']
            skip_interface = args["interface"] and not fnmatch.fnmatch(interface, args["interface"])
            #if skip_interface:
            #    print("Skipping interface %s" % interface)
            if tree:
                if depth == 3 and not skip_interface:
                    if not service_printed:
                        print_service_pid_command(cursor)
                        service_printed=True
                    if not object_printed:
                        print("\t%s" % object_path)
                        object_printed=True
                    print("\t\t%s" % interface)
            elif not skip_interface:
                print("%s\t%s" % (service, object_path), end="")
                if depth == 3:
                    print("\t%s" % interface, end="")
                if args["pid"]:
                    print("\t%s" % cursor["pid"], end="")
                if args["command_line"]:
                    print("\t%s" % cursor["command_line"], end="")
                print()
    for new_path in subobjects:
        service_printed = rec_intro(bus, service, new_path, cursor, service_printed)
    return service_printed


for service in connections:
    if not args["all"] and service.startswith(':'): continue
    if not fnmatch.fnmatch(service, args["service"]):
        continue
    if service == myname:  # Don't query about ourself
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
            if depth == 1:
                print_service_pid_command(cursor)
            if depth > 1:
                rec_intro(bus, service, "/", cursor)
        else:
            if depth == 1:
                print_service_pid_command(cursor, sep="\t")
            else:
                rec_intro(bus, service, "/", cursor)
    except KeyboardInterrupt as e:
        print(e)
        print("Got a keyboard exception in the main loop")
        sys.exit(1)

# Not used currently
def get_managed_object(service="org.bluez"):
    dbus_object = bus.get_object(service, "/")
    dbus_iface  = dbus.Interface(dbus_object, 'org.freedesktop.DBus.ObjectManager')
    L = dbus_iface.GetManagedObjects()
    return L
