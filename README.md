# SecureBMS — EV Battery Cell Telemetry & Degradation Analyzer

**Team Zerova · IBM Z Datathon 2026**
Hosted and executed on an **IBM LinuxONE (Ubuntu / s390x)** server.

SecureBMS is a battery-management-system (BMS) data pipeline for a single EV, single battery pack and single cell. It does two things:

1. **Generates** a synthetic 1000-second telemetry dataset (MATLAB) in which road speed-hump shocks physically damage the cell (microcracks → higher internal resistance → lower State of Health).
2. **Analyzes** that dataset (Python / Jupyter) to recover the electrical, thermal, mechanical and degradation parameters, quantify how much damage comes from shocks vs. normal cycling, and verify the cyber-security anomaly labels.

---

## Repository layout

```
SecureBMS/
├── README.md
├── requirements.txt
├── data/
│   └── SecureBMS_OneBattery_OneCell_1000.csv       # 1000 rows x 17 columns
├── src/
│   ├── SecureBMS_Data_Generator.m                  # MATLAB: creates the CSV
│   └── SecureBMS_Analyzer.py                       # Python: report + dashboard
├── notebooks/
│   └── SecureBMS_Analyzer.ipynb                    # same analysis as Jupyter cells
├── outputs/
│   ├── SecureBMS_Analysis_Report.txt               # console report
│   └── SecureBMS_Dashboard.png                     # 4-panel plot
└── docs/
    ├── SecureBMS_MATLAB_Data_Generator_Source.pdf  # original MATLAB live-script export
    ├── SecureBMS_Jupyter_Analysis_Output.pdf       # original Jupyter run on LinuxONE
    └── plots/                                      # the 4 individual dashboard panels
```

## Quick start

```bash
pip install -r requirements.txt

# Option A: script (headless-safe, saves outputs/SecureBMS_Dashboard.png)
python src/SecureBMS_Analyzer.py

# Option B: notebook
jupyter notebook notebooks/SecureBMS_Analyzer.ipynb
```

The analyzer auto-detects the CSV (current folder, `data/`, `../data/`, or `~/Zerova/`, the folder used on the LinuxONE server). To regenerate the data, run `src/SecureBMS_Data_Generator.m` in MATLAB (`rng(42)` makes it reproducible).

## Dataset (`SecureBMS_OneBattery_OneCell_1000.csv`)

1 Hz sampling, 1000 rows, 17 columns:

| Group | Columns |
|---|---|
| IDs | `timestamp`, `vehicle_id`, `battery_id`, `cell_id` |
| Vehicle | `speed_kmph`, `km_travelled`, `hump_event`, `humps_encountered` |
| Electrical | `current_A`, `voltage_V`, `soc_pct` |
| Thermal | `temperature_C` |
| Mechanical | `vibration_g` |
| Degradation | `microcrack_index`, `internal_resistance_mohm`, `soh_pct` |
| Label | `anomaly_label` (1 if R_int > 42 mΩ, T > 42 °C, or crack > 0.30 with V < 3.45) |

### Simulation model (MATLAB)

- **Speed** = 30 + 10·sin(t/80) + noise; **current** = 3 + 2·sin(t/35) + noise (min 0.1 A).
- **12 random speed humps**: vibration jumps from ~0.04 g to 1.2–2.8 g, and each hump adds 0.015–0.025 to the microcrack index.
- **Internal resistance** = 28 + 35·microcrack + 0.002·t + noise (mΩ).
- **SoC** from Coulomb counting on a 5 Ah cell; **OCV** = 3.0 + 1.2·SoC; **terminal voltage** = OCV − I·R.
- **Temperature** = 28 + 0.015·I² + 0.8·microcrack + noise; **SoH** = 100 − 4·microcrack − 0.0002·t.

## What the analyzer does

| Section | Computation |
|---|---|
| 1. Trip dynamics | Duration, distance, mean/min/max speed |
| 2. Electrical | SoC drop, Coulomb-counted charge, estimated nominal capacity, C-rate, reconstructed OCV (`V + I·R`) and its correlation with SoC |
| 3. Thermal | Temperature range, Joule heating `P = I²R`, T-vs-I correlation |
| 4. Mechanical | Hump timestamps, baseline vs. impact vibration, shock ratio |
| 5. Degradation | Microcrack / resistance growth, SoH loss split into shock vs. cycling, linear fits of R_int and SoH vs. microcracks |
| 6. Security | Anomaly-label verification (clean baseline run) |
| 7. Dashboard | 4-panel plot (speed/vibration, voltage/SoC, current/temperature, degradation) |

## Key results (from the LinuxONE run)

| Metric | Value |
|---|---|
| Duration / distance | 1000 s / 8.322 km (avg 29.96 km/h) |
| SoC | 89.99 % → 72.48 % (estimated capacity 5.00 Ah) |
| Temperature | 27.64 – 28.97 °C |
| Humps | 12; vibration 1.98 g vs 0.041 g baseline (**47.9×**) |
| Microcrack index | 0.020 → 0.257 (+1184.9 %) |
| Internal resistance | 28.92 → 39.19 mΩ (+35.5 %) |
| SoH loss | 1.148 % total, **82.8 % from hump shocks**, 17.2 % from normal cycling |
| Fits | R_int = 28.12 + 43.81·crack (R² 0.960); SoH = 99.99 − 4.90·crack (R² 0.994) |
| Anomalies | 0 of 1000 (benign baseline) |

**Takeaway:** a dozen speed humps in under 17 minutes cause most of the cell's degradation, and the microcrack index is a strong predictor of resistance growth and health loss. That makes vibration and resistance useful signals for a BMS to monitor.

## Dashboard

![SecureBMS dashboard](outputs/SecureBMS_Dashboard.png)

## Notes

- The dataset is **synthetic** (simulation for demonstration), not measured data.
- `anomaly_label` is all zeros, so this file is a clean baseline. Attack or fault-injected runs would be needed to train or test detection.
- All values are from a single cell and a single vehicle.

## Team

Team Zerova — IBM Z Datathon 2026
