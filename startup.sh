#!/bin/bash
nohup python3 web2py.py -a 'SO14uptane' -c server.crt -k server.key -i 127.0.0.1 -p 8000 &
