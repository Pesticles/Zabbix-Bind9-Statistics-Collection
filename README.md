# Zabbix Bind9 Statistics Collection

This method utilises Bind 9s built in statistics export via HTTP/XML.

Most statistics available are collected, several aggregate graphs are defined.

## To install:

* Copy the bind.conf into your zabbix agents include directory (/etc/zabbix/zabbix_agentd.d/ on Debian/Ubuntu)
* Copy the script z-bind-stats to /usr/bin/ (or anywhere else you like, but you will need to alter the contents of bind.conf)
* Import the xml template into Zabbix