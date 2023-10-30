#!/bin/sh 

## Automatically add myip to noip
## add crontab
## * */1 * * * sh /${home}/update-noip.sh > $HOME/cron.log 2>&1

USERNAME=
PASSWORD=
HOSTNAME=
MYIP=$(curl -s http://httpbin.org/ip | grep origin | awk '{print $2}' |         sed -e 's/"//g')
echo $MYIP
curl -s -u $USERNAME:$PASSWORD -o /dev/null "https://dynupdate.no-ip.com/nic/update?hostname=$HOSTNAME&myip=$MYIP"