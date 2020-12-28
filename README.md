# Nitor

A tool that automatically checks out letsencrypt cerificates and install them
in applications

Can be used for hosts not reachable over internet since it uses DNS for verification

Example:
If you have a domain name example.com. Create a subdomain and delegate this subdomain
to the computer running this tool

To avoid security issues, the nameserver on this machine is only running when requesting
and renewing certificates.

Note, if IPv6 is available, delegation using IPv6 is sufficient, no need to do any
port forwarding or similar in the firewall.

Developed and tested using Ubuntu 20.04


Installation and configuration
======================================

## Nitor server

### install acertmgr

    sudo apt install python3-pip
    sudo pip3 install acertmgr dnspython


### install nitor

    cd /opt
    git clone https://github.com/abundo/nitor.git


### Install isc-bind

    apt install bind9


### Create a zonefile

Create file /var/cache/bind/db.int.example.com with the below content

    $TTL 30
    @                       IN SOA  ns1.example.com. support.example.com. (
                                    1          ; serial
                                    604800     ; refresh (1 week)
                                    86400      ; retry (1 day)
                                    2419200    ; expire (4 weeks)
                                    30         ; minimum (30 seconds)
                                    )
    @                        NS      ns1.example.com.


### Allow dynamic update on the zone

Generate a key

    tsig-keygen -a HMAC-SHA256 acertmgr


Edit file /etc/bind/named.conf.local

Add the output from the above tsig-keygen command

Add the zone statement, for the domain you want certificates

Example content:

    key "acertmgr" {
            algorithm hmac-sha256;
            secret "yVUWQkzIqk/jP6z3Ihxdqbsp+/671/DELI3l4DHKoT4=";
    };

    zone "int.example.com" {
            type master;
            file "db.int.example.com";
            allow-update { key acertmgr; };
    };


Restart bind

    systemctl restart bind9


Verify that dynamic dns updates works

    nsupdate -l
    > key hmac-sha256:acertmgr yVUWQkzIqk/jP6z3Ihxdqbsp+/671/DELI3l4DHKoT4=
    > update add test.int.example.com 100 A 1.2.3.4
    > send

If no errors are displayed, remove the entry again

    > update delete test.int.example.com A
    > send

If the dynamic update of DNS does not work, you need to fix this before continuing.


Todo: Verify that delegation works



### configure acertmgr

edit /etc/acertmgr/acertmgr.conf

    ---
    authority_contact_email: anders@abundo.se
    authority-tos-agreement: true
    work-dir: /etc/acertmgr/workdir

    mode: dns.nsupdate
    dns_ttl: 30
    csr_static: true
    nsupdate_server: localhost
    nsupdate_keyname: acertmgr
    nsupdate_keyvalue: yVUWQkzIqk/jP6z3Ihxdqbsp+/671/DELI3l4DHKoT4=
    nsupdate_keyalgorithm: hmac-sha256


note, nsupdate_keyname, keyvalue and keyalgorithm must match whats in named.conf.local

Create directory for certificates

    mkdir /var/lib/nitor


Add domain names that should have get a certificates to /etc/acertmgr/domain.conf

Each domain has two entries.

    ---
    netbox.int.example.com:
    - path: /var/lib/nitor/netbox.int.example.com.key
      user: root
      group: root
      perm: '600'
      format: key
      action: /opt/nitor/nitor.py apache2 --hostname docker.int.example.se --cert-src netbox.int.example.com.key

    - path: /var/lib/nitor/netbox.int.example.com.crt
      user: root
      group: root
      perm: '600'
      format: crt,ca
      action: /opt/nitor/nitor.py apache2 --hostname docker.int.example.se --cert-src netbox.int.example.com.crt


Create a bash script /etc/acertmgr/periodic.sh

    #!/bin/bash
    systemctl start named.service

    sleep 10

    acertmgr

    systemctl stop named.service


### Configure cron, to periodically check and renew certs

Create file /etc/cron.d/nitor

    # SHELL=/bin/sh
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
    MAILTO=root
    22 3 * * * root /opt/nitor/periodic.sh >/tmp/nitor.output


### Setup ssh

Generate a ssh key for the remote hosts.

When asking for password, just press enter (no password)

    ssh-keygen -t rsa -b 4096 -f /root/.ssh/nitor


## Configure remote host

This needs to be done on each host that needs certificates.


### Remote host, add dedicated user for cert management

    sudo adduser nitor

as name, add "User for nitor cert management" or similar.


### Remote host, create directory for certificates

    sudo mkdir /etc/ssl/nitor
    sudo chown nitor /etc/ssl/nitor


### Remote host, grant permission to reload services when new cert is installed

Create a sudo file 

    visudo -f /etc/sudoers.d/nitor

 with the following content

    nitor    ALL=NOPASSWD: /bin/systemctl reload apache2.service


## nitor server
 
Copy key to remote host

    ssh-copy-id -i /root/.ssh/nitor nitor@netbox.int.example.com


Verify that remote login without password works

    ssh -i /root/.ssh/nitor nitor@netbox.int.example.com


Verify that apache2 can be reloaded, without password

    sudo /bin/systemctl reload apache2.service


## nitor server, checkout certificate and get it installed

    sudo acertmgr


# Troubleshooting

Todo

Error getting certificate

Error installing certificate

Error reloading application
