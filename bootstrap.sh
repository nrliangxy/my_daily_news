#!/usr/bin/env bash
/root/anaconda3/bin/pip install health360 -i http://192.168.3.115:4040/patsnapci/dev/+simple/  --trusted-host 192.168.3.115
ps aux | grep "manager_supervisord" | grep -v grep| cut -c 9-15 | xargs kill -9
supervisord -c manager_supervisord.conf