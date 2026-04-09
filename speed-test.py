#! /usr/bin/env python3


import sys
import os
import signal
from time import sleep
from datetime import datetime
import speedtest

loops = 1000
exception_delay = 3
loop_delay = 60
def sigint_handler(signal, frame):
    print("Shutting down")
    sys.exit(0)

def speed_test():
    st = speedtest.Speedtest()
    st.get_best_server()
    down  = round(st.download()/10**6,2)
    up = round(st.upload()/10**6,2)
    return datetime.now().isoformat(timespec='seconds'),st.results.dict()['ping'],down, up

signal.signal(signal.SIGINT, sigint_handler)

while [ 1 ]:
    try:
        dt,ping,down,up = speed_test()
        with open('data_file.csv', 'a') as df:
            df.write(f"{dt},{down},{up}\n")
            print(f"{dt} -> Download: {down:5.2f} Mb/s, Upload: {up:5.2f} Mb/s, Ping: {ping:.2f} ms")
    except Exception as ex:
        print (ex)
    sleep(loop_delay)
    loops = loops - 1
