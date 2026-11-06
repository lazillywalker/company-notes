#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
/usr/bin/python3 setup.py
printf '\nEnterで閉じます。'
read answer
