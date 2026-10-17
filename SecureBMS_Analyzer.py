# ==============================================================================
# SecureBMS: OneBattery OneCell Full Parameter & Degradation Analyzer
# Team Zerova | IBM Z Datathon 2026 | Run on IBM LinuxONE (Ubuntu), Python 3.8+
# Compatible with Jupyter Notebook / Linux / Python 3.8+
# ==============================================================================

# %% [imports]
import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib

try:  # running inside Jupyter?
    get_ipython()  # noqa: F821
    IN_NOTEBOOK = True
except NameError:
    IN_NOTEBOOK = False
if not IN_NOTEBOOK:
    matplotlib.use("Agg")  # headless server: save the figure to a file instead
import matplotlib.pyplot as plt

# %% [1. auto-detect & load dataset]
# ------------------------------------------------------------------------------
# 1. AUTO-DETECT & LOAD DATASET
# ------------------------------------------------------------------------------
TARGET_FILENAME = 'SecureBMS_OneBattery_OneCell_1000.csv'
CSV_PATH = None

# 1. Check direct and relative paths (including inside the repo's data/ and the
#    original Zerova folder used on the LinuxONE server)
candidate_paths = [
    TARGET_FILENAME,
    os.path.join('data', TARGET_FILENAME),
    os.path.join('..', 'data', TARGET_FILENAME),
    os.path.join('Zerova', TARGET_FILENAME),
    os.path.expanduser(f'~/Zerova/{TARGET_FILENAME}'),
    os.path.expanduser(f'~/{TARGET_FILENAME}'),
]

for path in candidate_paths:
    if os.path.exists(path):
        CSV_PATH = path
        break

# 2. If not found, search for any file starting with "SecureBMS_OneB" in current &
#    sub-folders
if CSV_PATH is None:
    search_patterns = [
        'SecureBMS_OneB*',
        'data/SecureBMS_OneB*',
        '../data/SecureBMS_OneB*',
        'Zerova/SecureBMS_OneB*',
        '*/SecureBMS_OneB*',
        os.path.expanduser('~/Zerova/SecureBMS_OneB*'),
    ]
    for pattern in search_patterns:
        matches = [f for f in glob.glob(pattern) if not f.endswith('.ipynb')]
        if matches:
            CSV_PATH = matches[0]
            break

if CSV_PATH is None:
    raise FileNotFoundError(
        f"Could not find '{TARGET_FILENAME}'.\n"
        f"Current Working Directory: {os.getcwd()}\n"
        f"Files in current folder: {os.listdir('.')}"
    )

print(f"Loaded dataset from: {os.path.abspath(CSV_PATH)}")
df = pd.read_csv(CSV_PATH)

print("=" * 80)
print(f" SECURE BMS ANALYSIS REPORT: {os.path.basename(CSV_PATH)}")
print("=" * 80)

# %% [2. vehicle trip dynamics]
# ------------------------------------------------------------------------------
# 2. VEHICLE TRIP DYNAMICS
# ------------------------------------------------------------------------------
duration_s = len(df)
duration_min = duration_s / 60.0
total_distance_km = df['km_travelled'].iloc[-1]
avg_speed = df['speed_kmph'].mean()
max_speed = df['speed_kmph'].max()
min_speed = df['speed_kmph'].min()

print("\n[1] VEHICLE DYNAMICS & TRIP PROFILE")
print(f"  • Total Duration       : {duration_s} seconds ({duration_min:.2f} minutes)")
print(f"  • Total Distance       : {total_distance_km:.3f} km")
print(f"  • Average Speed        : {avg_speed:.2f} km/h")
print(f"  • Speed Range          : {min_speed:.2f} km/h - {max_speed:.2f} km/h")

# %% [3. electrical characteristics & capacity estimation]
# ------------------------------------------------------------------------------
# 3. ELECTRICAL CHARACTERISTICS & CAPACITY ESTIMATION
# ------------------------------------------------------------------------------
soc_start = df['soc_pct'].iloc[0]
soc_end = df['soc_pct'].iloc[-1]
delta_soc = soc_start - soc_end

# Coulomb counting: Ah = sum(current * dt) / 3600   (dt = 1 s)
total_as = df['current_A'].sum()
total_ah = total_as / 3600.0
nominal_capacity_ah = total_ah / (delta_soc / 100.0)

avg_current = df['current_A'].mean()
max_current = df['current_A'].max()
min_current = df['current_A'].min()
avg_c_rate = avg_current / nominal_capacity_ah
peak_c_rate = max_current / nominal_capacity_ah

# Reconstruct Open Circuit Voltage (OCV): V_ocv = V_terminal + I * R_int
df['ocv_est_V'] = df['voltage_V'] + df['current_A'] * (df['internal_resistance_mohm'] / 1000.0)

corr_raw_v_soc = df['voltage_V'].corr(df['soc_pct'])
corr_ocv_soc = df['ocv_est_V'].corr(df['soc_pct'])

print("\n[2] ELECTRICAL PARAMETERS & CELL SPECIFICATIONS")
print(f"  • State of Charge (SoC): Starts at {soc_start:.2f}%, Ends at {soc_end:.2f}% (Drop: {delta_soc:.2f}%)")
print(f"  • Total Charge Drawn   : {total_ah:.4f} Ah ({total_as:.1f} A*s)")
print(f"  • Nominal Cell Capacity: {nominal_capacity_ah:.2f} Ah ({nominal_capacity_ah * 1000:.0f} mAh)")
print(f"  • Discharge Current    : Mean={avg_current:.2f} A, Max={max_current:.2f} A, Min={min_current:.2f} A")
print(f"  • Discharge C-Rate     : Mean={avg_c_rate:.2f}C, Peak={peak_c_rate:.2f}C")
print(f"  • Terminal Voltage     : Mean={df['voltage_V'].mean():.4f} V, "
      f"Range=[{df['voltage_V'].min():.4f} V, {df['voltage_V'].max():.4f} V]")
print(f"  • Reconstructed OCV    : Mean={df['ocv_est_V'].mean():.4f} V, "
      f"Range=[{df['ocv_est_V'].min():.4f} V, {df['ocv_est_V'].max():.4f} V]")
print(f"  • Correlation (V vs SoC)  : {corr_raw_v_soc:+.4f} (Raw Terminal Voltage)")
print(f"  • Correlation (OCV vs SoC): {corr_ocv_soc:+.4f} (Ohmic Drop Compensated)")

# %% [4. thermal dynamics & joule heating]
# ------------------------------------------------------------------------------
# 4. THERMAL DYNAMICS & JOULE HEATING
# ------------------------------------------------------------------------------
temp_min = df['temperature_C'].min()
temp_max = df['temperature_C'].max()
temp_mean = df['temperature_C'].mean()
delta_temp = temp_max - temp_min

# Joule heating power: P_loss = I^2 * R
df['joule_power_W'] = (df['current_A'] ** 2) * (df['internal_resistance_mohm'] / 1000.0)
corr_temp_current = df['temperature_C'].corr(df['current_A'])
corr_temp_power = df['temperature_C'].corr(df['joule_power_W'])

print("\n[3] THERMAL DYNAMICS")
print(f"  • Temperature Range    : {temp_min:.2f} °C to {temp_max:.2f} °C (Delta: {delta_temp:.2f} °C)")
print(f"  • Mean Temperature     : {temp_mean:.2f} °C")
print(f"  • Correlation (T vs I) : {corr_temp_current:+.4f} (Strong Joule heating dependence)")
print(f"  • Mean Internal Heat   : {df['joule_power_W'].mean():.3f} W (Peak: {df['joule_power_W'].max():.3f} W)")

# %% [5. mechanical stress & speed hump events]
# ------------------------------------------------------------------------------
# 5. MECHANICAL STRESS & SPEED HUMP EVENTS
# ------------------------------------------------------------------------------
hump_indices = df[df['hump_event'] == 1].index.tolist()
hump_timestamps = df.loc[hump_indices, 'timestamp'].tolist()
num_humps = len(hump_indices)

vib_baseline = df[df['hump_event'] == 0]['vibration_g']
vib_humps = df[df['hump_event'] == 1]['vibration_g']
vib_spike_ratio = vib_humps.mean() / vib_baseline.mean()

print("\n[4] MECHANICAL STRESS & ROAD ANOMALIES")
print(f"  • Hump Events Count    : {num_humps} road humps encountered")
print(f"  • Hump Timestamps (s)  : {hump_timestamps}")
print(f"  • Baseline Vibration   : Mean={vib_baseline.mean():.4f} g (Max={vib_baseline.max():.4f} g)")
print(f"  • Impact Vibration     : Mean={vib_humps.mean():.4f} g (Min={vib_humps.min():.4f} g, Max={vib_humps.max():.4f} g)")
print(f"  • Vibration Shock Ratio: {vib_spike_ratio:.1f}x higher during speed hump impact")

# %% [6. electro-mechanical degradation: SoH, microcracks & resistance]
# ------------------------------------------------------------------------------
# 6. ELECTRO-MECHANICAL DEGRADATION: SOH, MICROCRACKS & RESISTANCE
# ------------------------------------------------------------------------------
mc_start = df['microcrack_index'].iloc[0]
mc_end = df['microcrack_index'].iloc[-1]
mc_growth_pct = ((mc_end - mc_start) / mc_start) * 100.0

r_start = df['internal_resistance_mohm'].iloc[0]
r_end = df['internal_resistance_mohm'].iloc[-1]
r_growth_pct = ((r_end - r_start) / r_start) * 100.0

soh_start = df['soh_pct'].iloc[0]
soh_end = df['soh_pct'].iloc[-1]
total_soh_drop = soh_start - soh_end

# Decompose SoH loss: shock vs continuous
soh_diffs = df['soh_pct'].shift(1) - df['soh_pct']
hump_soh_loss = soh_diffs[df['hump_event'] == 1].sum()
normal_soh_loss = soh_diffs[df['hump_event'] == 0].sum()

pct_loss_shock = (hump_soh_loss / total_soh_drop) * 100.0
pct_loss_normal = (normal_soh_loss / total_soh_drop) * 100.0
avg_drop_per_hump = hump_soh_loss / num_humps
normal_rate_per_sec = normal_soh_loss / (len(df) - num_humps)

# Linear regression for R_int vs Microcracks
slope_r, intercept_r = np.polyfit(df['microcrack_index'], df['internal_resistance_mohm'], 1)
r2_r = np.corrcoef(df['microcrack_index'], df['internal_resistance_mohm'])[0, 1] ** 2

# Linear regression for SoH vs Microcracks
slope_soh, intercept_soh = np.polyfit(df['microcrack_index'], df['soh_pct'], 1)
r2_soh = np.corrcoef(df['microcrack_index'], df['soh_pct'])[0, 1] ** 2

print("\n[5] DEGRADATION & DAMAGE BREAKDOWN")
print(f"  • Microcrack Index     : {mc_start:.4f} -> {mc_end:.4f} (+{mc_growth_pct:.1f}% increase)")
print(f"  • Internal Resistance  : {r_start:.2f} mOhm -> {r_end:.2f} mOhm (+{r_growth_pct:.1f}% increase)")
print(f"  • Total SoH Loss       : {total_soh_drop:.4f}% ({soh_start:.4f}% -> {soh_end:.4f}%)")
print(f"    - Shock Loss (Humps) : {hump_soh_loss:.4f}% ({pct_loss_shock:.1f}% of total degradation)")
print(f"    - Cycling Loss       : {normal_soh_loss:.4f}% ({pct_loss_normal:.1f}% of total degradation)")
print(f"    - Avg Loss per Hump  : {avg_drop_per_hump:.6f}% per hump")
print(f"    - Normal Decay Rate  : {normal_rate_per_sec:.8f}% per second")
print(f"  • Resistance Model     : R_int = {intercept_r:.2f} + {slope_r:.2f} * Microcrack (R^2 = {r2_r:.3f})")
print(f"  • SoH Damage Model     : SoH = {intercept_soh:.2f} - {abs(slope_soh):.2f} * Microcrack (R^2 = {r2_soh:.3f})")

# %% [7. cyber-security / anomaly label verification]
# ------------------------------------------------------------------------------
# 7. CYBER-SECURITY / ANOMALY LABEL VERIFICATION
# ------------------------------------------------------------------------------
anomaly_counts = df['anomaly_label'].value_counts().to_dict()
print("\n[6] SECURITY & ANOMALY DETECTION (SecureBMS)")
print(f"  • Anomaly Label Counts : {anomaly_counts}")
if set(df['anomaly_label'].unique()) == {0}:
    print("  • Verification Status  : CLEAN BENIGN RUN. Zero cyber-attacks or anomalous sensor faults.")
    print("  • Operational Role     : Baseline reference profile for normal harsh-road operation.")

print("\n" + "=" * 80)
print(" ANALYSIS COMPLETE")
print("=" * 80)

# %% [8. visualization dashboard]
# ------------------------------------------------------------------------------
# 8. JUPYTER NOTEBOOK VISUALIZATION DASHBOARD
# ------------------------------------------------------------------------------
fig, axs = plt.subplots(4, 1, figsize=(12, 16), sharex=True)
plt.subplots_adjust(hspace=0.25)

# Plot 1: Speed & Vibration (Impact Events)
ax1 = axs[0]
ax1.plot(df['timestamp'], df['speed_kmph'], color='tab:blue', label='Speed (km/h)', alpha=0.8)
ax1.set_ylabel('Speed (km/h)', color='tab:blue')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax1_twin = ax1.twinx()
ax1_twin.plot(df['timestamp'], df['vibration_g'], color='tab:red', label='Vibration (g)', alpha=0.7)
ax1_twin.scatter(df.loc[hump_indices, 'timestamp'], df.loc[hump_indices, 'vibration_g'],
                 color='darkred', s=40, zorder=5, label='Hump Shock')
ax1_twin.set_ylabel('Vibration (g)', color='tab:red')
ax1_twin.tick_params(axis='y', labelcolor='tab:red')
ax1.set_title('Vehicle Speed & Mechanical Vibration Spikes', fontweight='bold')
ax1.grid(True, alpha=0.3)

# Plot 2: Terminal Voltage & OCV vs SoC
ax2 = axs[1]
ax2.plot(df['timestamp'], df['voltage_V'], color='tab:purple', label='Terminal Voltage (V)', alpha=0.9)
ax2.plot(df['timestamp'], df['ocv_est_V'], color='tab:orange', linestyle='--', label='Compensated OCV (V)')
ax2.set_ylabel('Voltage (V)')
ax2.legend(loc='upper right')

ax2_twin = ax2.twinx()
ax2_twin.plot(df['timestamp'], df['soc_pct'], color='tab:green', label='SoC (%)')
ax2_twin.set_ylabel('State of Charge (%)', color='tab:green')
ax2_twin.tick_params(axis='y', labelcolor='tab:green')
ax2.set_title('Voltage Curves & State of Charge (SoC) Depletion', fontweight='bold')
ax2.grid(True, alpha=0.3)

# Plot 3: Current & Temperature
ax3 = axs[2]
ax3.plot(df['timestamp'], df['current_A'], color='tab:brown', label='Current (A)', alpha=0.8)
ax3.set_ylabel('Discharge Current (A)', color='tab:brown')
ax3.tick_params(axis='y', labelcolor='tab:brown')

ax3_twin = ax3.twinx()
ax3_twin.plot(df['timestamp'], df['temperature_C'], color='tab:olive', label='Temperature (°C)', alpha=0.9)
ax3_twin.set_ylabel('Temperature (°C)', color='tab:olive')
ax3_twin.tick_params(axis='y', labelcolor='tab:olive')
ax3.set_title('Current Draw & Battery Cell Heating', fontweight='bold')
ax3.grid(True, alpha=0.3)

# Plot 4: Microcrack Index, Internal Resistance & SoH
ax4 = axs[3]
ax4.plot(df['timestamp'], df['internal_resistance_mohm'], color='darkorange', label='R_int (mOhm)')
ax4.plot(df['timestamp'], df['microcrack_index'] * 100, color='crimson', linestyle=':',
         label='Microcrack Index (x100)')
ax4.set_ylabel('Resistance (mOhm) / Damage', color='darkorange')
ax4.tick_params(axis='y', labelcolor='darkorange')
ax4.legend(loc='center left')

ax4_twin = ax4.twinx()
ax4_twin.plot(df['timestamp'], df['soh_pct'], color='tab:blue', linewidth=2, label='SoH (%)')
ax4_twin.set_ylabel('State of Health (%)', color='tab:blue')
ax4_twin.tick_params(axis='y', labelcolor='tab:blue')
ax4.set_title('Electro-Mechanical Degradation: Microcracks, Resistance Growth & SoH Loss', fontweight='bold')
ax4.set_xlabel('Timestamp (seconds)', fontweight='bold')
ax4.grid(True, alpha=0.3)

plt.tight_layout()

# Save the dashboard next to the report (useful on a headless LinuxONE server)
OUT_DIR = 'outputs' if os.path.isdir('outputs') else ('../outputs' if os.path.isdir('../outputs') else '.')
fig.savefig(os.path.join(OUT_DIR, 'SecureBMS_Dashboard.png'), dpi=150, bbox_inches='tight')
if IN_NOTEBOOK:
    plt.show()
