This is a small program to make queries about Dbus services, object paths and services. Although D-feet is a great program for browsing the Dbus tree, it doesn't for example allow finding all services that offer an interface.

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