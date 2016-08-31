# Zabbix Bind9 Statistics Collection

[![Join the chat at https://gitter.im/Zabbix-Bind9-Statistics-Collection/Lobby](https://badges.gitter.im/Zabbix-Bind9-Statistics-Collection/Lobby.svg)](https://gitter.im/Zabbix-Bind9-Statistics-Collection/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

This method utilises Bind 9s built in statistics export via HTTP/XML.

Most statistics available are collected, several aggregate graphs are defined.

[Forked from https://github.com/Pesticles/Zabbix-Bind9-Statistics-Collection](https://github.com/Pesticles/Zabbix-Bind9-Statistics-Collection)

## Requirements
* Zabbix 2.X.X and above
* Python 3


## To install:
* Configure Bind to export statistics via HTTP by adding the following to your bind.conf and restarting bind:
```
statistics-channels {
 	inet 127.0.0.1 port 8653 allow { 127.0.0.1; };
};
```
* Copy the userparameter_bind.conf into your zabbix agents include directory (/etc/zabbix/zabbix_agentd.d/ on
Debian/Ubuntu)
* Copy the script bind-stats.py to /usr/local/bin/ (or anywhere else you like, but you will need to alter the
contents of
userparameter_bind.conf)
* Import the xml template into Zabbix

## Note:

You can enable per-zone statistics (which will be automatically discovered) by adding the following clause to each zone definition in your bind.conf:
`zone-statistics yes;`
