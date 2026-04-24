#!/usr/bin/env python
"""
Real-Time Internet Speed Monitor
Runs speedtest-cli in a background thread and plots download speed live with matplotlib.

Requirements:
    pip install matplotlib speedtest-cli
"""

import threading
import time
import datetime
import queue

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import speedtest

# ── Configuration ────────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 60   # seconds between speed tests (min ~10 s recommended)
MAX_POINTS = 120              # rolling window of data points shown on the graph
# ─────────────────────────────────────────────────────────────────────────────

# Thread-safe queue: worker → main thread
result_queue: queue.Queue = queue.Queue()

# Storage for plot data
timestamps: list[datetime.datetime] = []
download_mbps: list[float] = []

# Status string displayed as the graph subtitle
status_message = "Initialising first speed test…"


# ── Background worker ─────────────────────────────────────────────────────────

def speedtest_worker() -> None:
    """Run speed tests in a loop and push results onto result_queue."""
    global status_message

    st = speedtest.Speedtest(secure=False)

    while True:
        try:
            status_message = "Finding best server…"
            st.get_best_server()

            status_message = "Testing download speed…"
            download_bits = st.download()
            mbps = download_bits / 1_000_000          # convert b/s → Mb/s

            result_queue.put(("ok", mbps))
            status_message = f"Last result: {mbps:.2f} Mb/s  |  next in {POLL_INTERVAL_SECONDS}s"

        except Exception as exc:
            result_queue.put(("err", str(exc)))
            status_message = f"Error: {exc}"

        time.sleep(POLL_INTERVAL_SECONDS)


# ── Matplotlib setup ──────────────────────────────────────────────────────────

plt.style.use("dark_background")

fig, ax = plt.subplots(figsize=(11, 5))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

(line,) = ax.plot([], [], color="#58a6ff", linewidth=2, zorder=3)
area = ax.fill_between([], [], alpha=0)          # rebuilt each frame

ax.set_title("Real-Time Internet Speed Monitor", color="#e6edf3",
             fontsize=15, fontweight="bold", pad=14)
subtitle = ax.text(0.5, 1.01, status_message,
                   transform=ax.transAxes, ha="center", va="bottom",
                   fontsize=9, color="#8b949e")

ax.set_xlabel("Time", color="#8b949e", labelpad=8)
ax.set_ylabel("Download Speed (Mb/s)", color="#8b949e", labelpad=8)
ax.tick_params(colors="#8b949e")
for spine in ax.spines.values():
    spine.set_edgecolor("#30363d")

ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
fig.autofmt_xdate(rotation=35)

ax.grid(True, color="#21262d", linewidth=0.7, zorder=0)


# ── Animation callback ────────────────────────────────────────────────────────

def update(_frame):
    global area

    # Drain everything the worker has sent since the last frame
    while not result_queue.empty():
        kind, payload = result_queue.get_nowait()
        if kind == "ok":
            timestamps.append(datetime.datetime.now())
            download_mbps.append(payload)

            # Keep rolling window
            if len(timestamps) > MAX_POINTS:
                timestamps.pop(0)
                download_mbps.pop(0)

    subtitle.set_text(status_message)

    if len(timestamps) < 2:
        return line, subtitle

    line.set_data(timestamps, download_mbps)

    # Rebuild the filled area (matplotlib requires this for dynamic data)
    area.remove()
    area = ax.fill_between(timestamps, download_mbps,
                           alpha=0.18, color="#58a6ff", zorder=2)

    ax.set_xlim(timestamps[0], timestamps[-1])
    margin = max(download_mbps) * 0.15 if max(download_mbps) > 0 else 5
    ax.set_ylim(0, max(download_mbps) + margin)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate(rotation=35)

    return line, subtitle


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Daemon thread dies automatically when the main process exits
    worker = threading.Thread(target=speedtest_worker, daemon=True)
    worker.start()

    ani = animation.FuncAnimation(
        fig, update,
        interval=1000,   # refresh plot every 1 s
        blit=False,      # blit=False lets us rebuild fill_between cleanly
        cache_frame_data=False,
    )

    plt.tight_layout()
    plt.show()
