#! /usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
import speedtest

data = [0 for i in range(60)]
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
        data.insert(0, down)
        data = data[:60]
    # pylint: disable=bare-except
    except:
        pass
    # pylint: enable=bare-except

x = [ i for i in range (60)]
plt.ion() # 1. Enable interactive mode
fig, ax = plt.subplots()
line, = ax.plot(x, data) # 2. Initialize plot object
ax.set_title = "Network Performace"
ax.set_xlabel= "Time"
ax.set_ylabel = "Mb/Sec"
for i in range(10):
    speed_test()
    print (data)
    line.set_xdata(data) # 3. Update data
    plt.pause(0.1) # 4. Refresh plot

