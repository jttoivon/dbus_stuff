#!/usr/bin/env python3

# A simple dbus program the joins either system or session bus and
# optionally registers a well-known name.
# It also exports the root object "/".
# The dbus-python library automatically adds the introspection interface to it.
# And we implement the Peer interface.

import sys
import argparse
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

parser = argparse.ArgumentParser(description='Query dbus tree')
parser.add_argument('-p','--pid',  action='store_true', default=False,  help='Show the process id that offers the service')
parser.add_argument('-c','--command-line',  action='store_true', default=False,  help='Show the command line of the process that offers the service')
parser.add_argument('--system',  action='store_true', default=True,  help='Query SystemBus (default)')
parser.add_argument('--session', action='store_true', default=False, help='Query SessionBus')
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Print debug information')
parser.add_argument('-s','--service', help='search pattern', required=False, default=None)
args = vars(parser.parse_args())

debug = args["debug"]

def get_machine_id():
    with open("/etc/machine-id") as f:
        return f.readline()

machine_id = get_machine_id()
print("Machine id is %s" % machine_id)

class Simple2(dbus.service.Object):
    def __init__(self, bus):
        self.path = "/"
        print("Registering object path %s" % self.path)
        dbus.service.Object.__init__(self, bus, self.path)

    # The org.freedesktop.DBus.Introspectable interface is defined
    # automatically by dbus-python. Let's implement
    # the interface org.freedesktop.DBus.Peer ourselves.
    @dbus.service.method("org.freedesktop.DBus.Peer",
        in_signature='',
        out_signature='')
    def Ping(self):
        print("Got ping!")
        return sum

    @dbus.service.method("org.freedesktop.DBus.Peer",
        in_signature='',
        out_signature='s')
    def GetMachineId(self):
        print("GetMachineId was called!")
        return machine_id

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

print(args.keys())

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

simple2 = Simple2(bus)
mainloop = GLib.MainLoop()
print("Starting event loop ...")
try:
    mainloop.run()
except KeyboardInterrupt:
    print("\nService stopped")
