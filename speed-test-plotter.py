#! /usr/bin/env python3
"""
collect network performace data
and plot it via gnuplot
"""

import sys
import signal
import subprocess
from time import sleep
import shutil
from typing import Any
import speedtest

SAMPLE_COUNT = 120
INTERVAL = 60
data = [0 for x in range(SAMPLE_COUNT)]

#pylint: disable=unused-argument:
def sigint_handler(sig: Any, frame: Any) -> None:
    """
    sigint handler to shutdown the app
    """
    print("Shutting down")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


def speed_test() -> None:
    """
    Collect speed test data and append to the data array
    """
    global data
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        down = round(st.download() / 10**6, 2)
        # up = round(st.upload()/10**6,2)
        data.insert(0,down)
        data = data[:SAMPLE_COUNT]
    # pylint: disable=bare-except
    except:
        pass
    # pylint: enable=bare-except


def plot_data() -> None:
    """
    Detects terminal size and plots numbers with custom labels.
    """
    speed_test()

    # 1. Determine Terminal Size
    size = shutil.get_terminal_size()
    width = size.columns
    height = max(5, size.lines - 2)  # Leave room for labels/prompt

    # 2. Prepare Data
    data_string = "\n".join(str(n) for n in data)

    # 3. Gnuplot Commands
    # 'set xlabel' and 'set ylabel' add the axis descriptions
    gnuplot_commands = [
        f"set terminal dumb size {width} {height}",
        'set ylabel "Mb/s"',
        'set xlabel "Minutes"',
        'plot "-" using 0:1 with lines title "Network Performance"',
        "set grid",
        data_string,
        "e",
    ]

    command_input = "\n".join(gnuplot_commands)

    try:
        subprocess.run(["gnuplot"], input=command_input, text=True, check=True)
    # pylint: disable=bare-except
    except:
        pass
    # pylint: enable=bare-except


if __name__ == "__main__":
    while 1:
        plot_data()
        try:
            avg = round(sum(data)/len([i for i in data if i != 0]),2)
        except:
            avg = 0
        _min = min([i for i in data if i != 0])
        _max = max([i for i in data if i != 0])
        _avg = round(sum([i for i in data if i != 0])/len([i for i in data if i != 0]),2)
        print(f"Samples: {SAMPLE_COUNT}  Last: {data[0]} : min: {_min} max: {_max} avg: {_avg}") 
        sleep(INTERVAL)
