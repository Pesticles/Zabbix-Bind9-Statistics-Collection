# Zabbix Bind9 Statistics Collection

This method utilises Bind 9s built in statistics export via HTTP/XML.

Most statistics available are collected, several aggregate graphs are defined.

## Requirements
* Python-argparse

## To install:
* Configure Bind to export statistics via HTTP by adding the following to your bind.conf and restarting bind:
```
statistics-channels {
 	inet 127.0.0.1 port 8053 allow { 127.0.0.1; };
};
```
* Copy the bind.conf into your zabbix agents include directory (/etc/zabbix/zabbix_agentd.d/ on Debian/Ubuntu)
* Copy the script z-bind-stats to /usr/bin/ (or anywhere else you like, but you will need to alter the contents of bind.conf)
* Import the xml template into Zabbix

## Note:

You can enable per-zone statistics (which will be automatically discovered) by adding the following clause to each zone definition in your bind.conf:
`zone-statistics yes;`
