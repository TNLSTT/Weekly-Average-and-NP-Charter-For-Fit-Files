import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from fitparse import FitFile
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "The 'fitparse' package is required. Install it with `pip install fitparse`."
    ) from exc


Record = Tuple[datetime, float]
RideMetrics = Dict[str, object]


def _extract_records(fit_path: str) -> List[Record]:
    """Return a list of (timestamp, power) tuples from a FIT file."""
    fitfile = FitFile(fit_path)
    fitfile.parse()

    records: List[Record] = []
    for record in fitfile.get_messages("record"):
        data = {field.name: field.value for field in record}
        timestamp = data.get("timestamp")
        power = data.get("power")
        if timestamp is None or power is None:
            continue
        records.append((timestamp, float(power)))

    return sorted(records, key=lambda item: item[0])


def _rolling_average(values: Sequence[float], window: int = 30) -> Iterable[float]:
    """Generate rolling averages with a given window size."""
    for idx in range(len(values)):
        start = idx - window + 1
        if start < 0:
            continue
        window_slice = values[start : idx + 1]
        yield sum(window_slice) / window


def _normalized_power(powers: Sequence[float]) -> float:
    """Compute Normalized Power following the 30s rolling average method."""
    rolling_avgs = list(_rolling_average(powers, window=30))
    if not rolling_avgs:
        return mean(powers) if powers else 0.0

    fourth_power_avg = mean([value**4 for value in rolling_avgs])
    return fourth_power_avg ** 0.25


def _noncoasting_average(powers: Sequence[float]) -> float:
    nonzero = [p for p in powers if p > 0]
    return mean(nonzero) if nonzero else 0.0


def _ride_energy_kj(records: Sequence[Record]) -> float:
    """Approximate total kilojoules using trapezoidal integration."""
    if len(records) < 2:
        return 0.0

    energy_joules = 0.0
    for (time_prev, power_prev), (time_curr, _) in zip(records, records[1:]):
        delta = (time_curr - time_prev).total_seconds()
        if delta <= 0:
            continue
        energy_joules += power_prev * delta

    return energy_joules / 1000.0


def analyze_ride(fit_path: str) -> Optional[RideMetrics]:
    records = _extract_records(fit_path)
    if not records:
        return None

    timestamps, powers = zip(*records)
    avg_power = mean(powers)
    metrics: RideMetrics = {
        "file": os.path.basename(fit_path),
        "start_time": timestamps[0],
        "avg_watts": avg_power,
        "avg_np": _normalized_power(powers),
        "avg_noncoasting_watts": _noncoasting_average(powers),
        "total_kj": _ride_energy_kj(records),
    }
    return metrics


def group_by_week(rides: Iterable[RideMetrics]) -> Dict[Tuple[int, int], List[RideMetrics]]:
    grouped: Dict[Tuple[int, int], List[RideMetrics]] = defaultdict(list)
    for ride in rides:
        iso_calendar = ride["start_time"].isocalendar()
        week_key = (iso_calendar[0], iso_calendar[1])
        grouped[week_key].append(ride)
    return grouped


def _mean(values: Sequence[float]) -> float:
    return mean(values) if values else 0.0


def summarize_week(week_key: Tuple[int, int], rides: Sequence[RideMetrics]) -> Dict[str, object]:
    return {
        "week": f"{week_key[0]}-W{week_key[1]:02d}",
        "avg_watts": _mean([ride["avg_watts"] for ride in rides]),
        "avg_np": _mean([ride["avg_np"] for ride in rides]),
        "avg_noncoasting_watts": _mean([ride["avg_noncoasting_watts"] for ride in rides]),
        "ride_count": len(rides),
        "total_kj": sum(ride["total_kj"] for ride in rides),
    }


def write_summary_csv(summary: Sequence[Dict[str, object]], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = [
        "week",
        "avg_watts",
        "avg_np",
        "avg_noncoasting_watts",
        "ride_count",
        "total_kj",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary:
            writer.writerow(row)


def summarize_directory(data_dir: str, output_path: str) -> Sequence[Dict[str, object]]:
    if os.path.isdir(data_dir):
        fit_files = sorted(
            [
                os.path.join(data_dir, name)
                for name in os.listdir(data_dir)
                if name.lower().endswith(".fit")
            ]
        )
    else:
        fit_files = []

    rides = []
    for fit_path in fit_files:
        ride_metrics = analyze_ride(fit_path)
        if ride_metrics:
            rides.append(ride_metrics)

    grouped = group_by_week(rides)
    weekly_summaries = [summarize_week(key, rides) for key, rides in sorted(grouped.items())]
    write_summary_csv(weekly_summaries, output_path)
    return weekly_summaries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze FIT files for weekly cycling power summaries."
    )
    parser.add_argument(
        "--data-dir", default="data", help="Directory containing .fit files (default: data)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("output", "weekly_summary.csv"),
        help="Output CSV path (default: output/weekly_summary.csv)",
    )

    args = parser.parse_args()

    summaries = summarize_directory(args.data_dir, args.output)
    if not summaries:
        print("No FIT files found or no usable data.")
    else:
        print(f"Wrote weekly summary to {args.output}")


if __name__ == "__main__":
    main()
