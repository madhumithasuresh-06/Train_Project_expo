#!/usr/bin/env python3
"""Generate RailSense datasets. See stations_data.py for station/corridor definitions."""

import csv
import math
import random
from pathlib import Path

from stations_data import CORRIDORS, get_unique_stations

random.seed(42)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ALL_DAYS = "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
WEEKDAYS = "Mon,Tue,Wed,Thu,Fri"
BOTTLENECK = {"MAS", "MS", "TPJ", "VM", "SA", "JTJ", "AJJ", "KPD", "MDU", "TEN"}

EXTRA = [
    ("SRV", "Srirangam", 10.86, 78.69, "SR", False),
    ("MNM", "Manamadurai", 9.69, 78.47, "SR", True),
    ("VPTN", "Virudhunagar", 9.59, 77.96, "SR", True),
    ("SCT", "Sattur", 9.36, 77.92, "SR", False),
    ("CVP", "Kovilpatti", 9.17, 77.87, "SR", True),
    ("TSI", "Tenkasi", 8.96, 77.31, "SR", True),
    ("NVL", "Neyveli", 11.54, 79.48, "SR", True),
    ("ULU", "Ulundurpet", 11.69, 79.32, "SR", True),
    ("ALU", "Ariyalur", 11.14, 79.08, "SR", True),
    ("PRN", "Perambalur", 11.23, 78.87, "SR", True),
    ("TVC", "Thiruvananthapuram Central", 8.487, 76.952, "SR", True),
]

TEMPLATES = [
    (40001, 12, "Chennai Beach EMU", "suburban", "chennai_suburban_south", ALL_DAYS, 38),
    (40501, 10, "Tambaram Local", "local", "tambaram_chengalpattu", ALL_DAYS, 36),
    (40521, 8, "Arakkonam EMU", "suburban", "chennai_suburban_north", ALL_DAYS, 40),
    (40601, 6, "Velachery MRTS", "suburban", "velachery_mrt", ALL_DAYS, 35),
    (12635, 1, "Vaigai Express", "superfast", "egmore_south", ALL_DAYS, 58),
    (12637, 1, "Pandian Express", "express", "egmore_south", ALL_DAYS, 50),
    (12653, 1, "Rockfort Express", "superfast", "egmore_chord", ALL_DAYS, 54),
    (12657, 1, "Chennai Mail", "superfast", "chennai_cbe_main", ALL_DAYS, 56),
    (12675, 1, "Kovai Express", "superfast", "chennai_cbe_main", ALL_DAYS, 54),
    (12607, 1, "Lalbagh Express", "superfast", "chennai_bengaluru", ALL_DAYS, 52),
    (12639, 1, "Brindavan Express", "superfast", "chennai_bengaluru", ALL_DAYS, 55),
    (76852, 8, "Villupuram Passenger", "passenger", "villupuram_pondy", ALL_DAYS, 35),
    (66001, 10, "Salem Passenger", "passenger", "erode_salem", ALL_DAYS, 38),
    (66031, 8, "Arakkonam Local", "local", "chennai_arakkonam", ALL_DAYS, 38),
    (66051, 10, "Gudur Passenger", "passenger", "chennai_gudur", ALL_DAYS, 45),
    (67201, 8, "Karaikkudi Passenger", "passenger", "karaikkudi_trichy", ALL_DAYS, 40),
    (67301, 12, "Bengaluru Local", "local", "bengaluru_mysuru", ALL_DAYS, 38),
    (67401, 8, "Arakkonam-Katpadi", "local", "arakkonam_katpadi", ALL_DAYS, 38),
    (67411, 8, "Perambur Suburban", "suburban", "perambur_suburban", ALL_DAYS, 36),
]

# Expand templates programmatically to ~396 trains
def expand_templates():
    out = list(TEMPLATES)
    n = 40000
    corridors = list(CORRIDORS.keys())
    types = ["superfast", "express", "passenger", "local"]
    names = ["Chennai Express", "TN SF", "Coromandel", "Kongu", "Pearl City", "Rockfort", "Pandian", "Cheran"]
    while len(out) < 180:
        c = corridors[n % len(corridors)]
        out.append((12600 + n, 1, names[n % len(names)], types[n % len(types)], c, ALL_DAYS, 48 + n % 12))
        n += 1
    return out


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = a[2], a[3], b[2], b[3]
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    x = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(x))


def fmt_time(m):
    m = int(m) % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def build_stations():
    base = get_unique_stations()
    seen = {s[0] for s in base}
    for s in EXTRA:
        if s[0] not in seen:
            base.append(s)
            seen.add(s[0])
    counter = 1
    by = {s[0]: s for s in base}
    for route in CORRIDORS.values():
        for i in range(len(route) - 1):
            if len(base) >= 245:
                break
            a, b = route[i], route[i + 1]
            if a not in by or b not in by:
                continue
            code = f"H{counter:03d}"
            if code in by:
                counter += 1
                continue
            sa, sb = by[a], by[b]
            lat = (sa[2] + sb[2]) / 2 + random.uniform(-0.005, 0.005)
            lon = (sa[3] + sb[3]) / 2 + random.uniform(-0.005, 0.005)
            base.append((code, f"{sa[1].split()[0]}-{sb[1].split()[0]} Halt", round(lat, 4), round(lon, 4), "SR", False))
            by[code] = base[-1]
            counter += 1
    return base[:245]


def schedule(tnum, route, smap, speed, ttype, reverse=False):
    codes = [c for c in (list(reversed(route)) if reverse else route) if c in smap]
    if len(codes) < 2:
        return []
    dwell = 1 if ttype in ("suburban", "local") else 2
    cur = random.randint(4, 20) * 60 + random.choice([0, 15, 30, 45])
    dist = 0.0
    segs = []
    for i, code in enumerate(codes):
        st = smap[code]
        if i == 0:
            arr, dep = "", fmt_time(cur)
        elif i == len(codes) - 1:
            arr, dep = fmt_time(cur), ""
        else:
            arr = fmt_time(cur)
            cur += dwell
            dep = fmt_time(cur)
        segs.append({"train_number": tnum, "stop_sequence": len(segs) + 1, "station_code": code,
                     "scheduled_arrival": arr, "scheduled_departure": dep, "distance_from_source_km": round(dist, 2)})
        if i < len(codes) - 1:
            ns = smap[codes[i + 1]]
            seg = haversine_km(st, ns) * 1.15
            dist += seg
            cur += (seg / speed) * 60
    return segs


def delays(tnum, ttype, route):
    base = {"superfast": (8, 18), "express": (10, 20), "local": (3, 10), "suburban": (2, 8), "passenger": (4, 12)}.get(ttype, (5, 15))
    bump = 5 if any(c in BOTTLENECK for c in route) else 0
    return [{"train_number": tnum, "day_of_week": d, "avg_delay_minutes": max(1, random.randint(*base) + bump + (3 if d in ("Sat", "Sun") else 0))} for d in DAYS]


def main():
    stations = build_stations()
    smap = {s[0]: s for s in stations}
    trains, segments, delays_rows = [], [], []
    used = set()
    for start, count, prefix, ttype, corridor, days, speed in expand_templates():
        route = [c for c in CORRIDORS.get(corridor, []) if c in smap]
        if len(route) < 2:
            continue
        for i in range(count):
            tnum = start + i
            while tnum in used:
                tnum += 1000
            used.add(tnum)
            rev = i % 2 == 1
            r = list(reversed(route)) if rev else route
            src, dst = r[0], r[-1]
            name = f"{prefix} {i + 1}" if count > 1 else prefix
            trains.append({"train_number": tnum, "train_name": name.strip(), "train_type": ttype,
                             "source_station": src, "destination_station": dst, "days_of_operation": days})
            segs = schedule(tnum, route, smap, speed, ttype, rev)
            segments.extend(segs)
            delays_rows.extend(delays(tnum, ttype, route))

    served = {s["station_code"] for s in segments}
    next_num = max(t["train_number"] for t in trains) + 1
    majors = [c for c in ["MAS", "MS", "TBM", "TPJ", "SA", "CBE", "MDU", "AJJ", "VM"] if c in smap]
    for st in stations:
        if st[0] in served:
            continue
        major = majors[0]
        route = [major, st[0]] if st[0] != major else [major, majors[1]]
        trains.append({"train_number": next_num, "train_name": f"Shuttle {st[1][:20]}", "train_type": "passenger",
                       "source_station": route[0], "destination_station": route[-1], "days_of_operation": ALL_DAYS})
        segments.extend(schedule(next_num, route, smap, 35, "passenger"))
        delays_rows.extend(delays(next_num, "passenger", route))
        next_num += 1

    with open(DATA_DIR / "stations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["station_code", "station_name", "latitude", "longitude", "zone", "is_junction"])
        for s in stations:
            w.writerow([s[0], s[1], s[2], s[3], s[4], str(s[5]).lower()])
    for fname, rows, fields in [
        ("trains.csv", trains, ["train_number", "train_name", "train_type", "source_station", "destination_station", "days_of_operation"]),
        ("segments.csv", segments, ["train_number", "stop_sequence", "station_code", "scheduled_arrival", "scheduled_departure", "distance_from_source_km"]),
        ("delay_profile.csv", delays_rows, ["train_number", "day_of_week", "avg_delay_minutes"]),
    ]:
        with open(DATA_DIR / fname, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fields).writeheader()
            csv.DictWriter(f, fieldnames=fields).writerows(rows)

    print(f"stations.csv: {len(stations)} | trains.csv: {len(trains)} | segments.csv: {len(segments)} | delay_profile.csv: {len(delays_rows)}")


if __name__ == "__main__":
    main()
