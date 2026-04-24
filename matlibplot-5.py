#!/usr/bin/env python
"""
Real-Time Internet Speed Monitor
Runs speedtest-cli in a background thread and plots download AND upload speed
live with matplotlib.
Features:
  • Download line (blue) + upload line (purple)
  • Per-series dashed average lines
  • Min / max callout annotations per series
  • Stats summary box (min / avg / max) for both series

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
MAX_POINTS = 180             # rolling window of data points shown on the graph

# ─────────────────────────────────────────────────────────────────────────────

# Thread-safe queue: worker → main thread
# Payload: ("ok", download_mbps, upload_mbps) | ("err", message)
result_queue: queue.Queue = queue.Queue()

# Storage for plot data
timestamps:    list[datetime.datetime] = []
download_mbps: list[float] = []
upload_mbps:   list[float] = []

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
            dl_bits = st.download()

            status_message = "Testing upload speed…"
            ul_bits = st.upload()

            dl = dl_bits / 1_000_000
            ul = ul_bits / 1_000_000

            result_queue.put(("ok", dl, ul))
            status_message = (
                f"↓ {dl:.2f}  ↑ {ul:.2f} Mb/s  |  next in {POLL_INTERVAL_SECONDS}s"
            )

        except Exception as exc:
            result_queue.put(("err", str(exc)))
            status_message = f"Error: {exc}"

        time.sleep(POLL_INTERVAL_SECONDS)


# ── Matplotlib setup ──────────────────────────────────────────────────────────

plt.style.use("dark_background")

fig, ax = plt.subplots(figsize=(18, 9))
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#161b22")

# Download line + fill
(dl_line,) = ax.plot([], [], color="#0c451a", linewidth=2, zorder=3, label="Download")
dl_area = ax.fill_between([], [], alpha=0)       # rebuilt each frame

# Upload line + fill
(ul_line,) = ax.plot([], [], color="#7a0c06", linewidth=2, zorder=3, label="Upload")
ul_area = ax.fill_between([], [], alpha=0)       # rebuilt each frame

# Average lines (dashed)
(dl_avg_line,) = ax.plot([], [], color="#0c451a", linewidth=1.4,
                         linestyle="--", zorder=4, alpha=0.75, label="DL Avg")
(ul_avg_line,) = ax.plot([], [], color="#7a0c06", linewidth=1.4,
                         linestyle="--", zorder=4, alpha=0.75, label="UL Avg")

ax.set_title("Real-Time Internet Speed Monitor", color="#e6edf3",
             fontsize=15, fontweight="bold", pad=14)
subtitle = ax.text(0.5, 1.01, status_message,
                   transform=ax.transAxes, ha="center", va="bottom",
                   fontsize=9, color="#8b949e")

ax.set_xlabel("Time", color="#8b949e", labelpad=8)
ax.set_ylabel("Speed (Mb/s)", color="#8b949e", labelpad=8)
ax.tick_params(colors="#8b949e")
for spine in ax.spines.values():
    spine.set_edgecolor("#30363d")

ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
fig.autofmt_xdate(rotation=35)
ax.grid(True, color="#21262d", linewidth=0.7, zorder=0)

# Legend
ax.legend(loc="upper left", facecolor="#161b22",
          edgecolor="#30363d", labelcolor="#e6edf3", fontsize=9)

# Stats summary box
stats_text = ax.text(
    0.99, 0.97, "",
    transform=ax.transAxes,
    ha="right", va="top",
    fontsize=9, color="#e6edf3",
    linespacing=1.7,
    fontfamily="monospace",
    bbox=dict(boxstyle="round,pad=0.55", facecolor="#21262d",
              edgecolor="#30363d", alpha=0.92),
    zorder=5,
)

# Point annotations rebuilt each frame
dl_min_ann = dl_max_ann = None
ul_min_ann = ul_max_ann = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_annotation(ax, label, value, ts, offset_y, color):
    """Create a single annotated callout pointing at (ts, value)."""
    va = "top" if offset_y < 0 else "bottom"
    return ax.annotate(
        f"{label}\n{value:.2f}",
        xy=(ts, value),
        xytext=(0, offset_y),
        textcoords="offset points",
        ha="center", va=va,
        fontsize=8, color=color,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=0.8),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#21262d",
                  edgecolor=color, alpha=0.85),
        zorder=6,
    )


# ── Animation callback ────────────────────────────────────────────────────────

def update(_frame):
    global dl_area, ul_area
    global dl_min_ann, dl_max_ann, ul_min_ann, ul_max_ann

    # Drain everything the worker has sent since the last frame
    while not result_queue.empty():
        item = result_queue.get_nowait()
        if item[0] == "ok":
            _, dl, ul = item
            timestamps.append(datetime.datetime.now())
            download_mbps.append(dl)
            upload_mbps.append(ul)

            if len(timestamps) > MAX_POINTS:
                timestamps.pop(0)
                download_mbps.pop(0)
                upload_mbps.pop(0)

    subtitle.set_text(status_message)

    if len(timestamps) < 2:
        return dl_line, ul_line, dl_avg_line, ul_avg_line, subtitle, stats_text

    # ── Derived stats ────────────────────────────────────────────────────────
    dl_avg = sum(download_mbps) / len(download_mbps)
    dl_min = min(download_mbps);  dl_min_i = download_mbps.index(dl_min)
    dl_max = max(download_mbps);  dl_max_i = download_mbps.index(dl_max)

    ul_avg = sum(upload_mbps) / len(upload_mbps)
    ul_min = min(upload_mbps);    ul_min_i = upload_mbps.index(ul_min)
    ul_max = max(upload_mbps);    ul_max_i = upload_mbps.index(ul_max)

    overall_max = max(dl_max, ul_max)

    # ── Lines ────────────────────────────────────────────────────────────────
    dl_line.set_data(timestamps, download_mbps)
    ul_line.set_data(timestamps, upload_mbps)
    dl_avg_line.set_data(timestamps, [dl_avg] * len(timestamps))
    ul_avg_line.set_data(timestamps, [ul_avg] * len(timestamps))

    # ── Fills ────────────────────────────────────────────────────────────────
    dl_area.remove()
    dl_area = ax.fill_between(timestamps, download_mbps,
                              alpha=0.12, color="#0c451a", zorder=2)
    ul_area.remove()
    ul_area = ax.fill_between(timestamps, upload_mbps,
                              alpha=0.12, color="#7a0c06", zorder=2)

    # ── Axes limits ──────────────────────────────────────────────────────────
    ax.set_xlim(timestamps[0], timestamps[-1])
    margin = overall_max * 0.20 if overall_max > 0 else 5
    ax.set_ylim(0, overall_max + margin)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate(rotation=35)

    # ── Stats box ────────────────────────────────────────────────────────────
    stats_text.set_text(
        f"         {'↓ DL':>10}  {'↑ UL':>10}\n"
        f"▲ Max  {dl_max:>10.2f}  {ul_max:>10.2f}\n"
        f"◆ Avg  {dl_avg:>10.2f}  {ul_avg:>10.2f}\n"
        f"▼ Min  {dl_min:>10.2f}  {ul_min:>10.2f}"
    )

    # ── Point annotations ────────────────────────────────────────────────────
    for ann in (dl_min_ann, dl_max_ann, ul_min_ann, ul_max_ann):
        if ann is not None:
            ann.remove()

    dl_min_ann = make_annotation(ax, "DL Min", dl_min, timestamps[dl_min_i], -42, "#ff7b72")
    dl_max_ann = make_annotation(ax, "DL Max", dl_max, timestamps[dl_max_i], +42, "#3fb950")
    ul_min_ann = make_annotation(ax, "UL Min", ul_min, timestamps[ul_min_i], -42, "#d2a8ff")
    ul_max_ann = make_annotation(ax, "UL Max", ul_max, timestamps[ul_max_i], +42, "#e6b8f0")

    return dl_line, ul_line, dl_avg_line, ul_avg_line, subtitle, stats_text


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    worker = threading.Thread(target=speedtest_worker, daemon=True)
    worker.start()

    ani = animation.FuncAnimation(
        fig, update,
        interval=1000,
        blit=False,
        cache_frame_data=False,
    )

    plt.tight_layout()
    plt.show()
