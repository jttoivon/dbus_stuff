# Some random dbus utilities

This repository provides three example dbus clients or servers, implemented using
the [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/index.html) module. On Ubuntu this module can be installed for Python3 with
`sudo apt install dbus-python3`.

## simple.py

This utility joins either system or session bus and stays attached until control-c is pressed.
It can optionally request a well-known name. Usage:

    ./simple.py [--session ]

or

    ./simple.py [--session] --service com.example.simple

The latter example requests a well-known name `com.example.simple`. Note that normally
user can only specify the well-known name freely, if the session bus is specified.
If you want to name a service on the system bus, then you need to allow this by
creating a config file that defines the needed permission. There is an example
configuration file `com.example.simple.conf` that you can enable by copying
it to the directory `/etc/dbus-1/system.d`.

This utility exists as an example of a dbus client and also for testing purposes.

## simple2.py

This utility expands the functionality of simple.py. It exports a root object "/" and starts
an event loop that waits for incoming method execution requests and answers them.
The dbus-python automatically defines the `org.freedesktop.DBus.Introspectable` interface for us,
so if a client calls its `introspect` method an XML description of our object is returned.

An accompanying conf file `com.example.simple2.conf` is provided.

This utility exists as an example of a dbus server and also for testing purposes.

## query.py

This is a small program to make queries about dbus services, object paths and services. Although D-feet is a great program for browsing the dbus tree, it doesn't for example allow finding all services that offer a given interface.

To see a description of the command line options call with ```./query.py -h```.

Without any parameters it lists the available services. By default the used bus is the system bus. Use the ```--session``` option to change that.

    ./query.py

To search only for services in the org.freedesktop namespace you can use 
    ./query.py --service 'org.freedesktop.*'

Similarly, you can pass --object-path and --interface option the define glob patterns for these. If no options or just the --service option is given, then only services will be printed. If --object-path option is given, then both service name and object path is printed. Finally, if --interface option is given, then all three are printed: service, object path and interface. If the filter pattern for higher levels in the hierarchy are not given but a lower one is, they are assumed to be '*'. The following example demonstrates this.

Find all services and object paths that implement the ObjectManager interface:

    ./query.py --interface org.freedesktop.DBus.ObjectManager

By default the output is in tree form. The next example requests for the output as a table.
Show service and object path pairs that implement the Bluetooth profile interface:

    ./query.py --table --all --interface org.bluez.Profile1  --pid --command-line

The --all option above asks to print also don't services that don't have a well known name. This can sometimes cause timeout problems, since some services don't implement the introspection interface. I set timeout of two seconds by default, but if you want the program execution to be faster,
you can set the timeout to any real number with the ```--timeout``` option. 