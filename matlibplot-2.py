#!/usr/bin/env python3

"""
float_animator.py
=================
An animated matplotlib application that:
  1. Takes an array of floats as input
  2. Graphs the array in real-time
  3. Iterates over the data in a loop, altering values over time

Controls (keyboard shortcuts while the window is open):
  SPACE  – pause / resume the animation
  R      – reset to original data
  Q/Esc  – quit

Usage examples
--------------
  # Default built-in dataset
  python float_animator.py

  # Pass your own floats via CLI
  python float_animator.py 1.0 3.5 2.2 8.7 4.1 6.3 0.9 5.5
"""

import sys
import math
import random
import argparse
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import animation
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec
import numpy as np
import speedtest

# resolved colormaps – avoids pylint no-member on plt.cm / matplotlib.cm
_CMAP_COOL   = matplotlib.colormaps.get_cmap("cool")
_CMAP_AUTUMN = matplotlib.colormaps.get_cmap("autumn")

# ── colour palette ────────────────────────────────────────────────────────────
BG_DARK   = "#0d1117"
BG_PANEL  = "#161b22"
ACCENT    = "#58a6ff"
ACCENT2   = "#3fb950"
ACCENT3   = "#f78166"
GRID_COL  = "#21262d"
TEXT_COL  = "#c9d1d9"
BAR_EDGE  = "#1f6feb"

# ── default dataset ────────────────────────────────────────────────────────────
DEFAULT_DATA: list[float] = [
    3.14, 1.59, 2.65, 3.58, 9.79, 3.23, 8.46, 2.64,
    3.38, 3.27, 9.50, 2.88, 4.19, 7.16, 9.39, 9.37,
    5.10, 5.82, 0.97, 4.94, 4.59, 2.30, 7.81, 6.40,
]

# ── available transform modes ──────────────────────────────────────────────────
MODES = [
    "sine_wave",
    "random_walk",
    "decay",
    "growth",
    "ripple",
]


# ─────────────────────────────────────────────────────────────────────────────
class FloatAnimator:
    """Manages state and renders the animated chart."""

    def __init__(self, data: list[float]):
        self.original   = list(data)
        self.data       = list(data)
        self.n          = len(data)
        self.frame      = 0
        self.paused     = False
        self.mode_idx   = 0

        # per-element phase offsets for wave effects
        self.phases = [random.uniform(0, 2 * math.pi) for _ in range(self.n)]

        self._build_figure()
        self._connect_events()

    # ── figure construction ────────────────────────────────────────────────────
    def _build_figure(self):
        plt.rcParams.update({
            "figure.facecolor":  BG_DARK,
            "axes.facecolor":    BG_PANEL,
            "axes.edgecolor":    GRID_COL,
            "axes.labelcolor":   TEXT_COL,
            "xtick.color":       TEXT_COL,
            "ytick.color":       TEXT_COL,
            "text.color":        TEXT_COL,
            "grid.color":        GRID_COL,
            "font.family":       "monospace",
        })

        self.fig = plt.figure(figsize=(14, 8), facecolor=BG_DARK)
        self.fig.canvas.manager.set_window_title("Float Animator")

        gs = GridSpec(2, 1, figure=self.fig,
                      hspace=0.45, wspace=0.35,
                      left=0.07, right=0.97,
                      top=0.88, bottom=0.10)

        # ① bar chart – current values
        #self.ax_bar  = self.fig.add_subplot(gs[0, :])
        # ② line chart – value over frames for element 0
        self.ax_line = self.fig.add_subplot(gs[1, 0])
        # ③ scatter – index vs value
        #self.ax_scat = self.fig.add_subplot(gs[1, 1])

        self._style_axes()

        # history buffer for the line chart
        self.history_len = 120
        self.history     = [self.data[0]] * self.history_len

        # ── initial artists ────────────────────────────────────────────────────
        x = range(self.n)

        #self.bars = self.ax_bar.bar(
        #    x, self.data,
        #    color=ACCENT, edgecolor=BAR_EDGE, linewidth=0.6,
        #)

        self.line_plot, = self.ax_line.plot(
            range(self.history_len), self.history,
            color=ACCENT2, linewidth=1.5,
        )

        #self.scatter_plot = self.ax_scat.scatter(
        #    x, self.data,
        #    c=[self._val_to_color(v) for v in self.data],
        #    s=60, edgecolors=BAR_EDGE, linewidths=0.5, zorder=3,
        #)

        # title / status
        self.title = self.fig.suptitle(
            "Float Animator  ·  SPACE pause  ·  R reset  ·  Q quit",
            color=TEXT_COL, fontsize=11, y=0.97,
        )
        #self.mode_text = self.ax_bar.set_title(
        #    f"Mode: {MODES[self.mode_idx]}   frame: 0",
        #    color=ACCENT, fontsize=9, loc="right",
        #)

        # labels
        #self.ax_bar.set_xlabel("index", fontsize=8)
        #self.ax_bar.set_ylabel("value",  fontsize=8)
        self.ax_line.set_title("element[0] over time", color=TEXT_COL, fontsize=8)
        self.ax_line.set_xlabel("frame", fontsize=7)
        self.ax_line.set_ylabel("value", fontsize=7)
        #self.ax_scat.set_title("index vs value (scatter)", color=TEXT_COL, fontsize=8)
        #self.ax_scat.set_xlabel("index", fontsize=7)
        #self.ax_scat.set_ylabel("value", fontsize=7)

    def _style_axes(self):
        pass
        #for ax in (self.ax_bar, self.ax_line, self.ax_scat):
        #    ax.set_facecolor(BG_PANEL)
        #    ax.tick_params(labelsize=7)
        #    ax.grid(True, linestyle="--", alpha=0.4)
        #    for spine in ax.spines.values():
        #        spine.set_edgecolor(GRID_COL)

    # ── color mapping ──────────────────────────────────────────────────────────
    def _val_to_color(self, v: float) -> str:
        """Map a float to a hex colour between ACCENT and ACCENT3."""
        lo, hi = min(self.original), max(self.original)
        t = (v - lo) / (hi - lo + 1e-9)
        # lerp ACCENT ↔ ACCENT3 through ACCENT2
        if t < 0.5:
            return _CMAP_COOL(t * 2)
        return _CMAP_AUTUMN((t - 0.5) * 2)

    # ── data transforms ────────────────────────────────────────────────────────
    def _apply_transform(self):
        mode = MODES[self.mode_idx]
        t    = self.frame * 0.08

        if mode == "sine_wave":
            for i in range(self.n):
                amp = (max(self.original) - min(self.original)) * 0.4
                self.data[i] = self.original[i] + amp * math.sin(t + self.phases[i])

        elif mode == "random_walk":
            for i in range(self.n):
                step = random.gauss(0, 0.25)
                self.data[i] = max(0.1, self.data[i] + step)

        elif mode == "decay":
            factor = math.exp(-0.005 * self.frame)
            for i in range(self.n):
                self.data[i] = self.original[i] * factor + 0.5

        elif mode == "growth":
            factor = 1 + 0.3 * math.sin(t * 0.5) ** 2
            for i in range(self.n):
                self.data[i] = self.original[i] * factor

        elif mode == "ripple":
            center = (self.n / 2) + (self.n / 2) * math.sin(t * 0.3)
            for i in range(self.n):
                dist = abs(i - center)
                wave = math.cos(dist * 0.7 - t * 1.5)
                amp  = (max(self.original) - min(self.original)) * 0.35
                self.data[i] = self.original[i] + amp * wave * math.exp(-dist * 0.12)

    # ── animation callback ─────────────────────────────────────────────────────
    def _update(self, _frame):
        if self.paused:
            return

        self._apply_transform()
        self.frame += 1

        # cycle modes every 180 frames
        if self.frame % 180 == 0:
            self.mode_idx = (self.mode_idx + 1) % len(MODES)

        # update bar heights & colours
        y_vals = self.data
        lo, hi = min(y_vals), max(y_vals)
        norm   = mcolors.Normalize(lo, hi)
        cmap   = _CMAP_COOL

        speed_test()
        # update history / line
        self.history.append(self.data[0])
        self.history = self.history[-self.history_len:]
        self.line_plot.set_ydata(self.history)
        self.ax_line.set_ylim(0, max(self.history) + 0.3)

    # ── keyboard events ────────────────────────────────────────────────────────
    def _connect_events(self):
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _on_key(self, event):
        if event.key == " ":
            self.paused = not self.paused
        elif event.key == "r":
            self.data  = list(self.original)
            self.frame = 0
            self.history = [self.data[0]] * self.history_len
            print("↺ Reset to original data.")
        elif event.key in ("q", "escape"):
            plt.close("all")

    # ── run ────────────────────────────────────────────────────────────────────
    def run(self, interval_ms: int = 1000):
        """Start the animation event loop."""
        self._anim = animation.FuncAnimation(
            self.fig, self._update,
            interval=interval_ms, cache_frame_data=False,
        )
        print("\n✓ Float Animator running.")
        print("  SPACE  → pause / resume")
        print("  R      → reset data")
        print("  Q/Esc  → quit\n")
        plt.show()


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

if __name__ == "__main__":
    data = [ 0 for i in range(120)]

    animator = FloatAnimator(data)
    animator.run(interval_ms=10000)
