import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.interpolate import interp1d
from matplotlib.patches import Circle
import subprocess
import random
from fetch_data import fetch_owid_data
import json

# Load config for zoom, labels etc.
with open("config.json") as f:
    config = json.load(f)

# Parse CLI args
parser = argparse.ArgumentParser()
parser.add_argument("--metric", required=True)
parser.add_argument("--country", required=True)
args = parser.parse_args()

metric = args.metric
country = args.country

cfg = config.get(metric, {})
title = cfg.get("title", metric.replace("_", " ").title())
y_label = cfg.get("y_label", "Value")
zoom_max = cfg.get("zoom_max", None)

# Fetch data
df = fetch_owid_data(metric=metric, country=country)
x_vals = pd.to_datetime(df['date']).dt.year.to_numpy()
y_vals = df[metric].to_numpy()

# Interpolation
t = np.linspace(0, 1, 24 * 20)
t_eased = -(np.cos(np.pi * t) - 1) / 2
x_dense = t_eased * (x_vals[-1] - x_vals[0]) + x_vals[0]
interp = interp1d(x_vals, y_vals, kind='linear', fill_value="extrapolate")
y_dense = interp(x_dense)

# Set style
plt.rcParams.update({
    "font.size": 16,
    "axes.titleweight": "bold",
    "axes.labelsize": 16,
    "axes.titlesize": 20,
    "axes.edgecolor": "#333",
    "xtick.color": "#333",
    "ytick.color": "#333",
    "text.color": "#222",
    "figure.facecolor": "#f4f9ff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#f4f9ff",
})

fig, ax = plt.subplots(figsize=(6, 12))
ax.set_position([0.1, 0.2, 0.8, 0.75])
ax.set_xlim(x_vals[0], x_vals[-1])
ax.set_ylim(0, zoom_max or max(y_vals) * 1.2)
ax.set_title(f"{title} - {country}", pad=20)
ax.set_xlabel("Year")
ax.set_ylabel(y_label)

line, = ax.plot([], [], color="#2ca02c", lw=3)
dots = []

year_box = ax.text(
    0.5, 0.92, '', transform=ax.transAxes, ha='center', va='center',
    fontsize=30, fontweight='bold',
    bbox=dict(facecolor='black', alpha=0.5, boxstyle='round,pad=0.6'),
    color='white')

def update(frame):
    current_x = x_dense[frame]
    current_y = y_dense[frame]
    ax.set_ylim(0, max(current_y + 1, zoom_max or max(y_vals)))
    line.set_data(x_dense[:frame], y_dense[:frame])
    if frame % 10 == 0:
        dot = Circle((current_x, current_y), 0.15, color='#FF5722', alpha=0.8)
        ax.add_patch(dot)
        dots.append(dot)
    year_box.set_text(str(int(current_x)))
    return [line, year_box] + dots

ani = animation.FuncAnimation(fig, update, frames=len(x_dense), interval=1000/24, blit=True)

os.makedirs("output", exist_ok=True)
video_path = f"output/{metric}_{country}.mp4"
ani.save(video_path, fps=24)
plt.close(fig)

# Add music
bgm_dir = "assets/bgm"
bgm_files = [f for f in os.listdir(bgm_dir) if f.endswith(".mp3")]
bgm_path = os.path.join(bgm_dir, random.choice(bgm_files))
audio_faded = "output/faded_audio.mp3"

# Get video duration
def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)

duration = get_duration(video_path)
fade = 3

subprocess.run([
    "ffmpeg", "-y", "-i", bgm_path,
    "-af", f"afade=t=in:st=0:d={fade},afade=t=out:st={duration - fade}:d={fade},aloop=loop=-1:size=2e+09",
    "-t", str(duration), audio_faded
])

# Merge video and music
final_path = f"output/{metric}_{country}_with_music.mp4"
subprocess.run([
    "ffmpeg", "-y", "-i", video_path, "-i", audio_faded,
    "-c:v", "copy", "-c:a", "aac", "-shortest", final_path
])

print(f"✅ Video saved to: {final_path}")
