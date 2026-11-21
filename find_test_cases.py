"""
Analyze data to find ideal test cases for each recommendation level.

Level 1: Direct express/superfast with seats available
Level 2: Only direct local/passenger (no express), with seats
Level 3: No direct train at all, must use hub connection
Level 4: Trains exist but none arrive before delayed ETA, falls back to bus

Key logic (from recommendation.js):
- findDirectTrains filters: train_type matches, srcIdx < dstIdx in segments, 
  arrival <= deadline (delayedEta), seats > 0 for travelClass:day
- Level 1 checked first (EXPRESS_TYPES), then Level 2 (LOCAL_TYPES)
- Level 3: findCombinedJourneys (hub-based, uses ALL junction stations as hubs)
- Level 4: findBusAlternatives (checks bus_routes.csv, source==source, dest==dest)

The deadline = scheduledArrival at destination + effectiveDelay
effectiveDelay = manualDelayMinutes (if provided) else predicted

For Level 4, we need: 
  all trains serving source->dest have arrival > delayedEta
  AND bus_routes has source->dest entry with seats > 0
"""

import csv

def load_csv(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

def parse_time(t):
    if not t or not t.strip(): return None
    try:
        h, m = t.strip().split(':')
        return int(h) * 60 + int(m)
    except: return None

def mins_to_time(m):
    m = m % (24*60)
    return f"{m//60:02d}:{m%60:02d}"

stations_data = load_csv('data/stations.csv')
trains_data = load_csv('data/trains.csv')
segments_data = load_csv('data/segments.csv')
seat_data = load_csv('data/seat_availability.csv')
bus_data = load_csv('data/bus_routes.csv')
delay_data = load_csv('data/delay_profile.csv')

# Build indexes
station_map = {s['station_code']: s for s in stations_data}
train_map = {t['train_number']: t for t in trains_data}

segments_by_train = {}
for seg in segments_data:
    tn = seg['train_number']
    if tn not in segments_by_train:
        segments_by_train[tn] = []
    segments_by_train[tn].append(seg)
for tn in segments_by_train:
    segments_by_train[tn].sort(key=lambda x: int(x['stop_sequence']))

# seat: train:day:class -> seats
seats_index = {}
for s in seat_data:
    key = f"{s['train_number']}:{s['day_of_week']}:{s['class']}"
    seats_index[key] = int(s['available_seats'])

# delay: train:day -> avg_delay
delay_index = {}
for d in delay_data:
    key = f"{d['train_number']}:{d['day_of_week']}"
    delay_index[key] = float(d['avg_delay_minutes'])

EXPRESS_TYPES = {'express', 'superfast'}
LOCAL_TYPES = {'local', 'suburban', 'passenger'}

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def get_stop_index(stops, code):
    for i, s in enumerate(stops):
        if s['station_code'] == code:
            return i
    return -1

def get_dep_at(stops, code):
    for s in stops:
        if s['station_code'] == code:
            t = s['scheduled_departure'] or s['scheduled_arrival']
            return parse_time(t)
    return None

def get_arr_at(stops, code):
    for s in stops:
        if s['station_code'] == code:
            t = s['scheduled_arrival'] or s['scheduled_departure']
            return parse_time(t)
    return None

def normalize(val, ref):
    adj = val
    if adj < ref: adj += 24 * 60
    return adj

def find_direct_trains(src, dst, types, deadline=None, day='Mon', tclass='SL'):
    results = []
    for train in trains_data:
        if train['train_type'] not in types: continue
        stops = segments_by_train.get(train['train_number'], [])
        si = get_stop_index(stops, src)
        di = get_stop_index(stops, dst)
        if si == -1 or di == -1 or si >= di: continue
        dep = get_dep_at(stops, src)
        arr = get_arr_at(stops, dst)
        if dep is None or arr is None: continue
        arr_adj = normalize(arr, dep)
        if deadline is not None:
            dl_adj = normalize(deadline, dep)
            if arr_adj > dl_adj: continue
        key = f"{train['train_number']}:{day}:{tclass}"
        seats = seats_index.get(key, None)
        if seats is None or seats <= 0: continue
        results.append({
            'train': train,
            'dep': dep,
            'arr': arr,
            'seats': seats,
        })
    return results

print("=" * 70)
print("LEVEL 1 — Find routes with direct express/superfast trains")
print("=" * 70)
# Need: at least one express/superfast between src->dst
# Best example: well-known long distance pair, pick one with obvious express

# Let's check which pairs have direct express trains
pairs_with_express = {}
for train in trains_data:
    if train['train_type'] not in EXPRESS_TYPES: continue
    stops = segments_by_train.get(train['train_number'], [])
    if len(stops) < 2: continue
    for i, s1 in enumerate(stops):
        for j, s2 in enumerate(stops):
            if j <= i: continue
            pair = (s1['station_code'], s2['station_code'])
            if pair not in pairs_with_express:
                pairs_with_express[pair] = []
            pairs_with_express[pair].append(train)

# Find a clean L1 pair: MAS->MDU (Vaigai, Rockfort, etc.)
test_pairs_l1 = [('MAS', 'MDU'), ('MS', 'MDU'), ('MAS', 'CBE'), ('MAS', 'TPJ'), ('MAS', 'SBC')]
for src, dst in test_pairs_l1:
    results = find_direct_trains(src, dst, EXPRESS_TYPES, day='Mon', tclass='SL')
    if results:
        t = results[0]['train']
        print(f"  {src}->>{dst}: {len(results)} express trains available. Best: {t['train_name']} #{t['train_number']} dep={mins_to_time(results[0]['dep'])} seats={results[0]['seats']}")
        # Also check that a booked train for this route exists for the "Your train" field
        # The booked train must also serve this route (srcIdx < dstIdx)
        # Let's find a booked train that IS the express, so we need a delay > threshold to trigger alternatives
        break

print()
print("For Level 1 demo: MAS->MDU")
print("Booked train: 12635 Vaigai Express (it IS an express but we want alternatives)")
# Check 12635
t12635 = segments_by_train.get('12635', [])
print(f"  12635 stops: {[s['station_code'] for s in t12635]}")
# check 12653 Rockfort Express
t12653 = segments_by_train.get('12653', [])
print(f"  12653 stops: {[s['station_code'] for s in t12653]}")
# For L1: we need booked train to be delayed, and alternative express trains to be available
# booked: 12635 (Vaigai), route MS->MDU, delay > threshold
# alternatives: 12637 Pandian, 12653 Rockfort, etc.
# Let's verify Pandian serves MS->MDU
t12637 = segments_by_train.get('12637', [])
print(f"  12637 stops: {[s['station_code'] for s in t12637]}")

print()
print("=" * 70)
print("LEVEL 2 — Find routes with ONLY local/passenger (no express)")
print("=" * 70)
# Need: direct local but NO direct express between src and dst
# Karaikkudi<->TPJ is local only (Karaikkudi Passenger)
test_pairs_l2 = [
    ('KKDI', 'TPJ'), ('TPJ', 'KKDI'),
    ('ED', 'SA'), ('SA', 'ED'),
    ('NCJ', 'TEN'),
    ('AJJ', 'KPD'),
    ('MDU', 'RMM'),
]
for src, dst in test_pairs_l2:
    exp = find_direct_trains(src, dst, EXPRESS_TYPES, day='Mon', tclass='SL')
    loc = find_direct_trains(src, dst, LOCAL_TYPES, day='Mon', tclass='SL')
    if not exp and loc:
        t = loc[0]['train']
        print(f"  GOOD L2: {src}->>{dst}: 0 express, {len(loc)} local. Best: {t['train_name']} #{t['train_number']} type={t['train_type']}")
    elif exp and loc:
        print(f"  Has express too: {src}->>{dst}: {len(exp)} express, {len(loc)} local")
    elif not exp and not loc:
        print(f"  Nothing direct: {src}->>{dst}")

print()
print("=" * 70)
print("LEVEL 3 — Find routes with NO direct trains at all")
print("=" * 70)
# We need a pair where there's no direct train (no row in segments covering both src and dst)
# Then verify a hub connection exists

def has_any_direct(src, dst, day='Mon', tclass='SL'):
    exp = find_direct_trains(src, dst, EXPRESS_TYPES, day=day, tclass=tclass)
    loc = find_direct_trains(src, dst, LOCAL_TYPES, day=day, tclass=tclass)
    return len(exp) + len(loc) > 0

# candidates: pairs between junction stations that likely have no direct service
junctions = [s['station_code'] for s in stations_data if s['is_junction'].lower() == 'true']
print(f"Junction count: {len(junctions)}")

# Known candidate pairs with no direct trains
candidate_l3 = [
    ('KKDI', 'TJ'),   # Karaikudi -> Thanjavur
    ('KKDI', 'MV'),   # Karaikudi -> Mayiladuthurai
    ('SVG', 'MAS'),   # Sivaganga -> Chennai
    ('TN', 'TPJ'),    # Thoothukudi -> Trichy
    ('RMM', 'NCJ'),   # Rameswaram -> Nagercoil
    ('RMM', 'CAPE'),  # Rameswaram -> Kanyakumari
    ('KRR', 'CBE'),   # Karur -> Coimbatore (no direct?)
    ('DG', 'CBE'),    # Dindigul -> Coimbatore
    ('VM', 'TPJ'),    # Villupuram -> Trichy
    ('TEN', 'CBE'),   # Tirunelveli -> Coimbatore
    ('VLR', 'MAS'),   # Vellore -> Chennai (no direct express?)
    ('VLR', 'CBE'),
    ('KPD', 'CBE'),   # Katpadi -> Coimbatore
    ('NVL', 'TPJ'),   # Neyveli -> Trichy
]

for src, dst in candidate_l3:
    exp = find_direct_trains(src, dst, EXPRESS_TYPES, day='Mon', tclass='SL')
    loc = find_direct_trains(src, dst, LOCAL_TYPES, day='Mon', tclass='SL')
    if not exp and not loc:
        print(f"  GOOD L3 candidate: {src}->>{dst}: NO direct trains at all")

print()
print("=" * 70)
print("LEVEL 4 — Bus fallback: trains exist but none arrive before delayedETA")
print("=" * 70)
# Bus routes: MAS->MDU, MDU->MAS, MAS->CBE, CBE->MAS, MAS->TPJ, TPJ->MAS,
#             MDU->TEN, TEN->MDU, CBE->SA, SA->CBE, MDU->TPJ, TPJ->MDU, MAS->SA, SA->MAS

bus_pairs = set()
for bus in bus_data:
    if int(bus['available_seats']) > 0:
        bus_pairs.add((bus['source'], bus['destination']))
print(f"Bus pairs with available seats: {bus_pairs}")

# For Level 4, we need:
# 1. A booked train serving src->dst
# 2. The alternative trains serving src->dst all arrive AFTER the delayed ETA
# 3. Bus exists for that src->dst pair

# Strategy: pick a pair with buses, find all alternative trains and their latest arrival times
# Set manualDelay so that delayedETA = scheduledArr + delay is BEFORE all train arrivals

# Let's check MAS->MDU (most buses)
print()
print("--- Analyzing MAS->MDU for Level 4 ---")
# Find all express trains MAS->MDU
all_mas_mdu = find_direct_trains('MAS', 'MDU', EXPRESS_TYPES | LOCAL_TYPES, day='Mon', tclass='SL')
print(f"  Trains MAS->MDU: {len(all_mas_mdu)}")
if all_mas_mdu:
    # Sort by arrival
    for t in all_mas_mdu:
        print(f"    {t['train']['train_name']} #{t['train']['train_number']} dep={mins_to_time(t['dep'])} arr={mins_to_time(t['arr'])}")

# To trigger L4, we need delayedETA to be BEFORE all train arrivals
# The earliest train arrives at what time? Set delayedETA to just before that.
# delayedETA = scheduledArr(booked train) + manualDelay
# We need: scheduledArr(booked) + manualDelay < earliest_alternative_arr
# So: manualDelay < earliest_alternative_arr - scheduledArr(booked)
# For L4, we want manualDelay > threshold but delayedETA still before all alternatives...
# Actually wait -- if no trains arrive BEFORE delayedETA, they all fail the deadline filter
# deadline = delayedETA = scheduled_arr_at_dest + effectiveDelay
# train is kept if: train arrival <= deadline
# So for L4, we need: ALL alternative train arrivals > delayedETA
# i.e., ALL alternatives arrive LATER than our delayed arrival

# Let's think differently: pick booked train = 12635 Vaigai Express, MS->MDU, arrives MDU
# Then set manualDelay to a large value, making delayedETA very late (near midnight/early morning)
# That way, alternatives that arrive EARLIER (lower arr time) get rejected because
# normalize makes them seem later... Actually let me re-read the logic.

# normalizeComparison(value, reference): if value < reference, value += 24*60
# So arrival normalized relative to departure
# deadline normalized relative to departure
# if arr_adj > deadline_adj: SKIP
# So: if we set deadline to be VERY EARLY (e.g., 06:00 = 360 mins)
# and trains arrive at 19:00 (1140 mins)
# dep = say 08:00 (480 mins)
# arr_adj = normalize(1140, 480) = 1140 (already >= 480)
# deadline_adj = normalize(360, 480) = 360+1440 = 1800
# 1140 <= 1800 -> train passes! So very large delay doesn't help directly...

# Actually we need deadline to be LESS than arrival times
# If booked train: 12635 MS->MDU, dep MS: let's say departs 06:00
# arrives MDU at say 14:30 = 870 mins
# effectiveDelay = 120 mins -> delayedETA = 870+120 = 990 = 16:30
# Now check alternative trains: if they all arrive AFTER 16:30, they get filtered out
# But Vaigai arrives ~14:30 itself. Other trains?

# Let's find the exact times for 12635
t12635 = segments_by_train.get('12635', [])
ms_idx = get_stop_index(t12635, 'MS')
mdu_idx = get_stop_index(t12635, 'MDU')
if ms_idx != -1 and mdu_idx != -1:
    dep_ms = parse_time(t12635[ms_idx]['scheduled_departure'] or t12635[ms_idx]['scheduled_arrival'])
    arr_mdu = parse_time(t12635[mdu_idx]['scheduled_arrival'] or t12635[mdu_idx]['scheduled_departure'])
    print(f"\n  12635 MS dep={mins_to_time(dep_ms)}, MDU arr={mins_to_time(arr_mdu)}")
    # Set manualDelay such that delayedETA falls between all alternatives
    # Find all alternative express trains on MS->MDU
    all_alts = find_direct_trains('MS', 'MDU', EXPRESS_TYPES, day='Mon', tclass='SL')
    print(f"  Alternative express trains MS->MDU (excl booked): {len(all_alts)}")
    for t in sorted(all_alts, key=lambda x: x['arr']):
        arr_n = normalize(t['arr'], dep_ms)
        print(f"    {t['train']['train_name']} arr={mins_to_time(t['arr'])} (normalized={arr_n})")
    
    # For L4: delayedETA must exceed ALL alternative arrival times (normalized to dep_ms)
    # Find max normalized arrival among all alternatives
    if all_alts:
        max_arr_n = max(normalize(t['arr'], dep_ms) for t in all_alts)
        print(f"  Latest alternative normalized arr: {mins_to_time(max_arr_n % (24*60))}")
        needed_delay = max_arr_n - arr_mdu + 1
        print(f"  To push ALL alternatives out: manualDelay >= {needed_delay} min")
        print(f"  That gives delayedETA = {mins_to_time((arr_mdu + needed_delay) % (24*60))}")
        print(f"  NOTE: this must also exceed any local trains on same route")
        
        # Check local trains too
        all_alts_loc = find_direct_trains('MS', 'MDU', LOCAL_TYPES, day='Mon', tclass='SL')
        print(f"  Local trains MS->MDU: {len(all_alts_loc)}")

# Check MAS->CBE for L4
print()
print("--- Analyzing MAS->CBE for Level 4 ---")
t12657 = segments_by_train.get('12657', [])  # Chennai Mail MAS->CBE
mas_idx = get_stop_index(t12657, 'MAS')
cbe_idx = get_stop_index(t12657, 'CBE')
if mas_idx != -1 and cbe_idx != -1:
    dep_mas = parse_time(t12657[mas_idx]['scheduled_departure'] or t12657[mas_idx]['scheduled_arrival'])
    arr_cbe = parse_time(t12657[cbe_idx]['scheduled_arrival'] or t12657[cbe_idx]['scheduled_departure'])
    print(f"  12657 MAS dep={mins_to_time(dep_mas)}, CBE arr={mins_to_time(arr_cbe)}")
    all_alts = find_direct_trains('MAS', 'CBE', EXPRESS_TYPES, day='Mon', tclass='SL')
    print(f"  Alternative express MAS->CBE: {len(all_alts)}")
    for t in sorted(all_alts, key=lambda x: normalize(x['arr'], dep_mas)):
        arr_n = normalize(t['arr'], dep_mas)
        print(f"    {t['train']['train_name']} #{t['train']['train_number']} arr={mins_to_time(t['arr'])} (norm={arr_n})")
    if all_alts:
        max_arr_n = max(normalize(t['arr'], dep_mas) for t in all_alts)
        needed_delay = max_arr_n - arr_cbe + 1
        print(f"  To push ALL out: manualDelay >= {needed_delay} min")

# Check MAS->SA for L4 (buses exist, fewer trains)
print()
print("--- Analyzing MAS->SA for Level 4 ---")
all_mas_sa = find_direct_trains('MAS', 'SA', EXPRESS_TYPES, day='Mon', tclass='SL')
all_mas_sa_l = find_direct_trains('MAS', 'SA', LOCAL_TYPES, day='Mon', tclass='SL')
print(f"  MAS->SA: {len(all_mas_sa)} express, {len(all_mas_sa_l)} local")
# Find booked train for MAS->SA
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'MAS')
    di = get_stop_index(stops, 'SA')
    if si != -1 and di != -1 and si < di:
        dep = get_dep_at(stops, 'MAS')
        arr = get_arr_at(stops, 'SA')
        key = f"{train['train_number']}:Mon:SL"
        seats = seats_index.get(key, None)
        print(f"  {train['train_name']} #{train['train_number']} type={train['train_type']} dep={mins_to_time(dep) if dep else '?'} arr={mins_to_time(arr) if arr else '?'} seats={seats}")
