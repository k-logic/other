#!/bin/sh 

## Automatically add myip to noip

USERNAME=
PASSWORD=
HOSTNAME=
MYIP=$(curl -s http://httpbin.org/ip | grep origin | awk '{print $2}' |         sed -e 's/"//g')
echo $MYIP
curl -s -u $USERNAME:$PASSWORD -o /dev/null "https://dynupdate.no-ip.com/nic/update?hostname=$HOSTNAME&myip=$MYIP"