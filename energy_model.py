import sys
import pandas as pd
import re
import matplotlib.pyplot as plt

# Constants for energy modeling
DISK_READ = 0.2   # W
DISK_WRITE = 0.5  # W
CPU = 1.2         # W
NET = 0.4         # W/MB

# Input
csv_path = sys.argv[1]
log_path = sys.argv[2]
label = sys.argv[3]  # e.g., edge1 or cdn

# Load simulated request data
df = pd.read_csv(csv_path, names=["time_total", "size_download", "http_code"])
df['time_total'] = df['time_total'].astype(float)
df['size_MB'] = df['size_download'] / (1024 * 1024)

# Load NGINX access log
hits, misses = 0, 0
with open(log_path) as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 3:
            status = parts[2]
            if status == 'HIT':
                hits += 1
            elif status == 'MISS':
                misses += 1

total = hits + misses
avg_size = df['size_MB'].mean() or 0.001
avg_hit_time = df.iloc[:hits]['time_total'].mean() if hits else 0.01
avg_miss_time = df.iloc[hits:]['time_total'].mean() if misses else 0.05

# Energy estimation
energy_hit = hits * DISK_READ * avg_hit_time
energy_miss = misses * (NET * avg_size + DISK_WRITE * avg_miss_time + CPU * 0.01)
energy_total = energy_hit + energy_miss
energy_origin = total * (NET * avg_size + DISK_WRITE * avg_miss_time + CPU * 0.01)
if energy_origin == 0:
    efficiency = 0
else:
    efficiency = 100 * (1 - (energy_total / energy_origin))

# Print results
print(f"\n🔍 Scenario: {label}")
print(f"Total: {total}, HIT: {hits}, MISS: {misses}")
print(f"Energy used (cache): {energy_total:.4f} Ws")
print(f"Energy if all origin: {energy_origin:.4f} Ws")
print(f"Energy saved: {efficiency:.2f}%")

# Save to CSV for plotting later
df_out = pd.DataFrame([{
    "scenario": label,
    "hits": hits,
    "misses": misses,
    "energy_cache_ws": energy_total,
    "energy_origin_ws": energy_origin,
    "efficiency_percent": efficiency
}])
df_out.to_csv(f"{label}_energy.csv", index=False)

# Merge and plot if both are present
import os
if os.path.exists("edge1_energy.csv") and os.path.exists("cdn_energy.csv"):
    df1 = pd.read_csv("edge1_energy.csv")
    df2 = pd.read_csv("cdn_energy.csv")
    df_combined = pd.concat([df1, df2])
    df_combined.set_index("scenario")[["energy_cache_ws", "energy_origin_ws"]].plot.bar(
        ylabel="Energy (Ws)",
        title="Cache vs Origin Energy per Scenario",
        rot=0,
        color=["green", "red"]
    )
    plt.tight_layout()
    plt.savefig("energy_report.png")