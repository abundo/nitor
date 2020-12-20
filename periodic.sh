#!/bin/bash
systemctl start named.service

sleep 10

acertmgr

systemctl stop named.service
