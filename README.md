This repository processes .fit cycling files and generates weekly summaries of:

Average Power (W)

Average Normalized Power (NP)

Average Power While Not Coasting (power > 0)

Optional: Total riding time, total kJ, number of rides per week

The goal is to produce a Python script that analyzes many FIT files in a directory and outputs a weekly CSV, table, or chart.

📁 Input Format: FIT Files

FIT (.fit) is Garmin’s binary activity file format.

Each FIT file contains:

Records (each representing one sample, typically every second)

Session summary data

Lap data

The script only needs record-level data, which includes:

Field	Meaning
power	Instantaneous power in watts
heart_rate	HR in bpm (unused here)
timestamp	Exact datetime for each sample
cadence	RPM (optional)
speed	m/s (optional)
📐 Metric Definitions
1. Average Watts

The simple mean of all non-missing power values.

Avg_Watts = sum(power_samples) / number_of_samples

2. Normalized Power (NP)

NP is a rolling 30-second average raised to the 4th power:

NP = ( avg( (30s_rolling_average_power)^4 ) )^(1/4)


Definition steps:

Compute 30-second rolling averages.

Raise each value to the 4th power.

Mean the results.

Take the 4th-root.

NP is designed to represent metabolic strain more accurately than raw average power.

3. Average Watts While Not Coasting

Coasting = power = 0
We compute the mean only for samples where power > 0.

NonCoasting_Avg_Watts = sum(power > 0) / count(power > 0)


📌 This is extremely useful for:

Estimating your “actual muscular average”

Removing soft-pedaling sections

Comparing ride-to-ride effort more fairly

4. Weekly Aggregation

Each .fit file is assigned to a week using the ISO calendar week or a Sunday-to-Saturday rule.

For each week:

Weekly_Avg_Watts = mean(Avg_Watts of each ride)
Weekly_Avg_NP = mean(NP of each ride)
Weekly_Avg_NonCoasting_Watts = mean(NonCoasting_Avg_Watts of each ride)
Weekly_Total_kJ = sum(kJ of each ride)
Weekly_Ride_Count = count(rides)

🧪 Python Library Used

The project uses:

pip install fitparse


Or:

pip install garmin-fit-sdk


Either works — Codex can choose.

🧰 Directory Structure
/Weekly-Average-and-NP-Charter-For-Fit-Files
    ├── README.md
    ├── data/
    │     └── *.fit
    ├── weekly_metrics.py
    └── output/
          └── weekly_summary.csv

🚀 Expected Python Script Behavior

The Python program should:

Load all .fit files in ./data

Extract:

timestamps

power values

Compute per-ride metrics:

average watts

normalized power

average watts while moving

Group rides by week

Output:

CSV summary

(Optional) Matplotlib chart of the 3 weekly averages

Save results to ./output/weekly_summary.csv

📝 Example CSV Output
week,avg_watts,avg_np,avg_noncoasting_watts,ride_count,total_kj
2025-W41,182,201,214,6,4123
2025-W42,195,215,231,7,4610
2025-W43,188,207,222,5,3877
