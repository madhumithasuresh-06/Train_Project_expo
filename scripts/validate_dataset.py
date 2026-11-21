#!/usr/bin/env python3
"""Validate RailSense dataset consistency."""

import csv
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_csv(name):
    path = DATA_DIR / name
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_time(t):
    if not t or not t.strip():
        return None
    h, m = map(int, t.split(":"))
    return h * 60 + m


def main():
    errors = []
    stations = load_csv("stations.csv")
    trains = load_csv("trains.csv")
    segments = load_csv("segments.csv")
    delays = load_csv("delay_profile.csv")

    station_codes = {s["station_code"] for s in stations}
    train_numbers = {t["train_number"] for t in trains}
    seg_trains = {s["train_number"] for s in segments}
    delay_trains = {d["train_number"] for d in delays}

    for tn in train_numbers:
        if tn not in seg_trains:
            errors.append(f"Train {tn} missing from segments.csv")
        if tn not in delay_trains:
            errors.append(f"Train {tn} missing from delay_profile.csv")

    for seg in segments:
        if seg["station_code"] not in station_codes:
            errors.append(f"Unknown station {seg['station_code']} in segments for train {seg['train_number']}")

    by_train = defaultdict(list)
    for seg in segments:
        by_train[seg["train_number"]].append(seg)

    for tn, stops in by_train.items():
        stops.sort(key=lambda x: int(x["stop_sequence"]))
        prev_dist = -1
        prev_time = None
        for i, stop in enumerate(stops):
            dist = float(stop["distance_from_source_km"])
            if dist < prev_dist - 0.01:
                errors.append(f"Train {tn}: distance decreases at stop {stop['stop_sequence']}")
            prev_dist = dist

            arr = parse_time(stop["scheduled_arrival"])
            dep = parse_time(stop["scheduled_departure"])
            t = dep if dep is not None else arr
            if t is not None and prev_time is not None:
                # Allow midnight crossing (add 24h if time appears to go backward)
                adjusted = t
                if adjusted < prev_time - 60:
                    adjusted += 24 * 60
                if adjusted < prev_time - 1:
                    errors.append(f"Train {tn}: time goes backward at stop {stop['stop_sequence']}")
                prev_time = adjusted
            elif t is not None:
                prev_time = t

    if errors:
        print(f"VALIDATION FAILED ({len(errors)} errors):")
        for e in errors[:30]:
            print(f"  - {e}")
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more")
        sys.exit(1)

    print("VALIDATION PASSED")
    print(f"  Stations: {len(stations)}")
    print(f"  Trains: {len(trains)}")
    print(f"  Segments: {len(segments)}")
    print(f"  Delay profiles: {len(delays)}")


if __name__ == "__main__":
    main()
