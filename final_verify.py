"""
Final verification of all 4 levels with exact UI inputs.
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
    if m is None: return '??:??'
    m = int(m) % (24*60)
    return f"{m//60:02d}:{m%60:02d}"

def normalize(val, ref):
    adj = val
    if adj < ref: adj += 24 * 60
    return adj

stations_data = load_csv('data/stations.csv')
trains_data = load_csv('data/trains.csv')
segments_data = load_csv('data/segments.csv')
seat_data = load_csv('data/seat_availability.csv')
delay_data = load_csv('data/delay_profile.csv')
bus_data = load_csv('data/bus_routes.csv')

station_map = {s['station_code']: s for s in stations_data}
train_map = {t['train_number']: t for t in trains_data}
segments_by_train = {}
for seg in segments_data:
    tn = seg['train_number']
    if tn not in segments_by_train: segments_by_train[tn] = []
    segments_by_train[tn].append(seg)
for tn in segments_by_train:
    segments_by_train[tn].sort(key=lambda x: int(x['stop_sequence']))
seats_index = {}
for s in seat_data:
    key = f"{s['train_number']}:{s['day_of_week']}:{s['class']}"
    seats_index[key] = int(s['available_seats'])
delay_index = {}
for d in delay_data:
    key = f"{d['train_number']}:{d['day_of_week']}"
    delay_index[key] = float(d['avg_delay_minutes'])

EXPRESS_TYPES = {'express', 'superfast'}
LOCAL_TYPES = {'local', 'suburban', 'passenger'}

def get_stop_index(stops, code):
    for i, s in enumerate(stops):
        if s['station_code'] == code: return i
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

def find_direct(src, dst, types, deadline=None, day='Mon', tclass='SL', exclude=None):
    results = []
    for train in trains_data:
        if train['train_type'] not in types: continue
        if exclude and train['train_number'] == exclude: continue
        stops = segments_by_train.get(train['train_number'], [])
        si = get_stop_index(stops, src)
        di = get_stop_index(stops, dst)
        if si == -1 or di == -1 or si >= di: continue
        dep = get_dep_at(stops, src)
        arr = get_arr_at(stops, dst)
        if dep is None or arr is None: continue
        if deadline is not None:
            arr_adj = normalize(arr, dep)
            dl_adj = normalize(deadline, dep)
            if arr_adj > dl_adj: continue
        key = f"{train['train_number']}:{day}:{tclass}"
        seats = seats_index.get(key, None)
        if seats is None or seats <= 0: continue
        results.append({'train': train, 'dep': dep, 'arr': arr, 'seats': seats})
    return results

# =====================
print("=" * 70)
print("LEVEL 1 VERIFICATION")
print("=" * 70)
# Route: MS -> MDU, booked on Vaigai Express 12635
# Need: delay > threshold -> system finds OTHER express trains on same route
# 12635 is MS->NCJ, it serves MS->MDU as an intermediate segment

# Check 12635 details
t12635_stops = segments_by_train.get('12635', [])
ms_i = get_stop_index(t12635_stops, 'MS')
mdu_i = get_stop_index(t12635_stops, 'MDU')
dep_ms = get_dep_at(t12635_stops, 'MS')
arr_mdu = get_arr_at(t12635_stops, 'MDU')
delay_12635 = delay_index.get('12635:Mon', None)
seats_12635_sl = seats_index.get('12635:Mon:SL', None)

print(f"Booked train: 12635 Vaigai Express")
print(f"  Route src=MS (Chennai Egmore), dst=MDU (Madurai)")
print(f"  Departure MS: {mins_to_time(dep_ms)}, Arrival MDU: {mins_to_time(arr_mdu)}")
print(f"  Delay profile Mon: {delay_12635} min, Seats SL Mon: {seats_12635_sl}")
print()

# Find express alternatives on MS->MDU (excluding 12635)
alts_l1 = find_direct('MS', 'MDU', EXPRESS_TYPES, day='Mon', tclass='SL', exclude='12635')
print(f"Alternative express trains on MS->MDU (excl 12635): {len(alts_l1)}")
for t in alts_l1:
    print(f"  #{t['train']['train_number']} {t['train']['train_name']} dep={mins_to_time(t['dep'])} arr={mins_to_time(t['arr'])} seats={t['seats']}")

# With delay_12635 = say 25 min and threshold = 15:
# effectiveDelay = 25, delayedETA = arr_mdu + 25
# The alternatives are found WITHOUT deadline filter (no constraint) as long as they arrive before delayedETA
# Actually: delayedETA IS the deadline for alternatives
# Let's check: with default delay profile, which alternatives pass?
if delay_12635 and arr_mdu:
    delayed_eta = arr_mdu + delay_12635
    print(f"\nWith natural delay ({delay_12635} min), delayedETA = {mins_to_time(delayed_eta)}")
    alts_with_deadline = find_direct('MS', 'MDU', EXPRESS_TYPES, deadline=delayed_eta, day='Mon', tclass='SL', exclude='12635')
    print(f"Alternatives passing deadline: {len(alts_with_deadline)}")
    for t in alts_with_deadline:
        print(f"  #{t['train']['train_number']} {t['train']['train_name']} arr={mins_to_time(t['arr'])} seats={t['seats']}")

print()
print("L1 UI INPUTS:")
print(f"  From: Chennai Egmore (MS)")
print(f"  To: Madurai (MDU)")
print(f"  Your Train: Vaigai Express · #12635 (superfast)")
print(f"  Class: Sleeper (SL)")
print(f"  Threshold: 15 min")
print(f"  Manual Delay: 20 (to override and guarantee trigger)")

print()
print("=" * 70)
print("LEVEL 2 VERIFICATION")
print("=" * 70)
# Route: KKDI -> TPJ  (Karaikudi -> Tiruchchirappalli)
# Only Karaikkudi Passengers (local type) run here, no express
src, dst = 'KKDI', 'TPJ'
exp_l2 = find_direct(src, dst, EXPRESS_TYPES, day='Mon', tclass='SL')
loc_l2 = find_direct(src, dst, LOCAL_TYPES, day='Mon', tclass='SL')
print(f"KKDI->TPJ express: {len(exp_l2)}, local: {len(loc_l2)}")

# The booked train must serve KKDI->TPJ
# Let's pick one of the Karaikkudi Passengers as the booked train
booked_l2 = None
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'KKDI')
    di = get_stop_index(stops, 'TPJ')
    if si == -1 or di == -1 or si >= di: continue
    key_d = f"{train['train_number']}:Mon"
    key_s = f"{train['train_number']}:Mon:2S"
    d = delay_index.get(key_d, None)
    s_2s = seats_index.get(key_s, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    s_sl = seats_index.get(key_sl, None)
    dep = get_dep_at(stops, 'KKDI')
    arr = get_arr_at(stops, 'TPJ')
    print(f"  Train serving KKDI->TPJ: #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay_Mon={d} seats_2S={s_2s} seats_SL={s_sl}")
    if d is not None and booked_l2 is None:
        booked_l2 = train['train_number']

print()
print(f"Booked train for L2: #{booked_l2}")
if booked_l2:
    stops_booked = segments_by_train.get(booked_l2, [])
    dep_b = get_dep_at(stops_booked, 'KKDI')
    arr_b = get_arr_at(stops_booked, 'TPJ')
    delay_b = delay_index.get(f"{booked_l2}:Mon", None)
    delayed_eta = (arr_b + 20) if arr_b else None  # manual delay 20 min
    print(f"  dep={mins_to_time(dep_b)}, arr={mins_to_time(arr_b)}, delay_profile={delay_b}")
    print(f"  With manualDelay=20: delayedETA={mins_to_time(delayed_eta)}")
    # Check alternatives with this deadline
    if delayed_eta:
        alts_exp = find_direct('KKDI', 'TPJ', EXPRESS_TYPES, deadline=delayed_eta, day='Mon', tclass='2S', exclude=booked_l2)
        alts_loc = find_direct('KKDI', 'TPJ', LOCAL_TYPES, deadline=delayed_eta, day='Mon', tclass='2S', exclude=booked_l2)
        print(f"  Express alternatives: {len(alts_exp)} -> will trigger L2 (0 express)")
        print(f"  Local alternatives: {len(alts_loc)}")
        for t in alts_loc:
            print(f"    #{t['train']['train_number']} {t['train']['train_name']} dep={mins_to_time(t['dep'])} arr={mins_to_time(t['arr'])} seats={t['seats']}")

print()
print("L2 UI INPUTS:")
print(f"  From: Karaikkudi (KKDI)")
print(f"  To: Tiruchchirappalli (TPJ)")
print(f"  Your Train: Karaikkudi Passenger 1 · #67201 (passenger)")
print(f"  Class: Second Seating (2S)")
print(f"  Threshold: 15 min")
print(f"  Manual Delay: 20")

print()
print("=" * 70)
print("LEVEL 3 VERIFICATION")
print("=" * 70)
# For L3, the BOOKED train must serve src AND dst directly
# But there must be no OTHER trains doing so (so L1/L2 finds 0 alternatives)
# AND hub-based connections must exist

# From the single_train_pairs analysis: Let's find a clear case
# TPJ->CDM had only one train (52620, 52647, 52674)
# Let's check TPJ->CDM
src3, dst3 = 'TPJ', 'CDM'
exp3 = find_direct(src3, dst3, EXPRESS_TYPES, day='Mon', tclass='SL')
loc3 = find_direct(src3, dst3, LOCAL_TYPES, day='Mon', tclass='SL')
print(f"TPJ->CDM: {len(exp3)} express, {len(loc3)} local trains with seats")
for t in exp3 + loc3:
    print(f"  #{t['train']['train_number']} {t['train']['train_name']} type={t['train']['train_type']}")

# How about MDU->RMM?
src3b, dst3b = 'MDU', 'RMM'
exp3b = find_direct(src3b, dst3b, EXPRESS_TYPES, day='Mon', tclass='SL')
loc3b = find_direct(src3b, dst3b, LOCAL_TYPES, day='Mon', tclass='SL')
print(f"\nMDU->RMM: {len(exp3b)} express, {len(loc3b)} local with seats Mon/SL")
for t in exp3b + loc3b:
    print(f"  #{t['train']['train_number']} {t['train']['train_name']} type={t['train']['train_type']}")

# MDU->RMM has 6 trains (all destinations from MDU)! Too many.
# We need a case with EXACTLY 1 train (so excluding it leaves 0)

# Let's look at the trains on TPJ->CDM more carefully
print()
print("All trains on TPJ->CDM:")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'TPJ')
    di = get_stop_index(stops, 'CDM')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'TPJ')
    arr = get_arr_at(stops, 'CDM')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_s = f"{train['train_number']}:Mon:SL"
    s = seats_index.get(key_s, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={s}")

# KPD->VLR: only 6 short-route trains, let's check
print()
print("All trains on KPD->VLR:")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'KPD')
    di = get_stop_index(stops, 'VLR')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'KPD')
    arr = get_arr_at(stops, 'VLR')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_s = f"{train['train_number']}:Mon:SL"
    s = seats_index.get(key_s, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={s}")

# Since KPD->VLR has 6 trains all named TN SF etc, they're all the same route
# If we book one, there are 5 others as alternatives -> L1 or L2, not L3
# We need a pair where the BOOKED train is the ONLY train

# Strategy: Find long express trains that have unique segment pairs
# Example: 12633 Kanyakumari Express: MAS->MS->TBM->CGL->VM->TPJ->MDU->TEN->NCJ->CAPE
# If we look at MS->VM: many trains serve it
# What about VM->DG? Let's check
print()
print("All trains on VM->DG:")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'VM')
    di = get_stop_index(stops, 'DG')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'VM')
    arr = get_arr_at(stops, 'DG')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    s = seats_index.get(key_sl, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={s}")

print()
print("All trains on TEN->NCJ:")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'TEN')
    di = get_stop_index(stops, 'NCJ')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'TEN')
    arr = get_arr_at(stops, 'NCJ')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    s = seats_index.get(key_sl, None)
    key_2s = f"{train['train_number']}:Mon:2S"
    s2s = seats_index.get(key_2s, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={s} seats_2S={s2s}")

# The key insight for L3: we pick booked train = one specific train on a route
# where that train serves src->dst, but there are NO OTHER trains on that exact pair
# Most of the multi-train pairs exist because there are many duplicates (52601, 52628, etc.)
# Let's find pairs where only 1 distinct named train serves them

# Actually let me try: SA->DPJ (Salem -> Dharmapuri)
print()
print("All trains on SA->DPJ (Salem -> Dharmapuri):")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'SA')
    di = get_stop_index(stops, 'DPJ')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'SA')
    arr = get_arr_at(stops, 'DPJ')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    s = seats_index.get(key_sl, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={s}")

print()
print("All trains on MDU->KKDI (Madurai -> Karaikudi):")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'MDU')
    di = get_stop_index(stops, 'KKDI')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'MDU')
    arr = get_arr_at(stops, 'KKDI')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    s = seats_index.get(key_sl, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={s}")

print()
print("All trains on MDU->SVG (Madurai -> Sivaganga):")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'MDU')
    di = get_stop_index(stops, 'SVG')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'MDU')
    arr = get_arr_at(stops, 'SVG')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    s = seats_index.get(key_sl, None)
    key_2s = f"{train['train_number']}:Mon:2S"
    s2s = seats_index.get(key_2s, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={s} seats_2S={s2s}")

# MDU->SVG has 12636 Sivaganga Passenger (the only one)
# If booked on 12636, excluding it means 0 alternatives -> should go to L3
# Hub: MDU -> TPJ -> ... or MDU -> KKDI -> ...
# Let's check what hub connections exist
print()
print("Checking hub connections for MDU->SVG via various hubs:")
src3c, dst3c = 'MDU', 'SVG'
for hub in ['TPJ', 'KKDI', 'MNM', 'VRI']:
    leg1_e = find_direct(src3c, hub, EXPRESS_TYPES, day='Mon', tclass='2S')
    leg1_l = find_direct(src3c, hub, LOCAL_TYPES, day='Mon', tclass='2S')
    leg2_e = find_direct(hub, dst3c, EXPRESS_TYPES, day='Mon', tclass='2S')
    leg2_l = find_direct(hub, dst3c, LOCAL_TYPES, day='Mon', tclass='2S')
    print(f"  Hub {hub}: MDU->hub: {len(leg1_e)}exp+{len(leg1_l)}loc, hub->SVG: {len(leg2_e)}exp+{len(leg2_l)}loc")

# Hmm, SVG connections are tough since it's a small station
# Let's check the hub approach more carefully
# findCombinedJourneys uses nearbySource (20km radius) + all junctions
# SVG is a junction, and from MDU there are many trains

# Actually the better L3 test: let's find the pair where ONLY 1 TRAIN exists
# and we BOOK that train, so excluding it leaves 0 alternatives
# Then hub connections for that route exist

# For L3, the engine:
# 1. Checks L1 (express on route, excl booked) -> 0
# 2. Checks L2 (local on route, excl booked) -> 0
# 3. Checks L3 hub combos
# 4. If L3 finds combos -> returns L3

# BEST L3 CASE: SA -> DPJ (Salem -> Dharmapuri)
# Only 1-3 trains serve it, once we exclude booked, none left
# Hub connections: SA -> SBC via... wait, is there a hub between SA and DPJ?
print()
print("Hub connections for SA->DPJ:")
for hub in ['SBC', 'HSRA', 'KPN', 'JTJ', 'CBE']:
    leg1 = find_direct('SA', hub, LOCAL_TYPES | EXPRESS_TYPES, day='Mon', tclass='SL')
    leg2 = find_direct(hub, 'DPJ', LOCAL_TYPES | EXPRESS_TYPES, day='Mon', tclass='SL')
    print(f"  Hub {hub}: SA->hub: {len(leg1)}, hub->DPJ: {len(leg2)}")

print()
print("=" * 70)
print("LEVEL 4 FINAL VERIFICATION: TPJ->MDU")
print("=" * 70)
# Cleaner test: TPJ->MDU, booked on 12635 Vaigai Express
# which has 9 alternative trains but they all arrive after a certain time
# With manualDelay=177, delayedETA = 21:09 + 177 = 00:06

booked_l4 = '12635'
src4, dst4 = 'TPJ', 'MDU'
t_stops = segments_by_train.get(booked_l4, [])
si = get_stop_index(t_stops, src4)
di = get_stop_index(t_stops, dst4)

if si != -1 and di != -1:
    dep_b = get_dep_at(t_stops, src4)
    arr_b = get_arr_at(t_stops, dst4)
    delay_b = delay_index.get(f"{booked_l4}:Mon", None)
    print(f"Booked: 12635 Vaigai Express, TPJ dep={mins_to_time(dep_b)}, MDU arr={mins_to_time(arr_b)}")
    print(f"Delay profile Mon: {delay_b}")
    
    # manualDelay = 177 gives delayedETA = 21:09 + 177 = 00:06 + 1 = 00:06 min = 6 min
    manual = 177
    delayed_eta = (arr_b + manual) % (24*60)
    print(f"Manual delay = {manual}: delayedETA = {mins_to_time(arr_b + manual)} = {mins_to_time(delayed_eta)} (wraps midnight)")
    
    # Check alternatives
    alts_exp = find_direct(src4, dst4, EXPRESS_TYPES, deadline=delayed_eta, day='Mon', tclass='SL', exclude=booked_l4)
    alts_loc = find_direct(src4, dst4, LOCAL_TYPES, deadline=delayed_eta, day='Mon', tclass='SL', exclude=booked_l4)
    print(f"  Alternatives with deadline {mins_to_time(delayed_eta)}: {len(alts_exp)} express, {len(alts_loc)} local")
    
    # Check bus alternatives
    buses = [b for b in bus_data if b['source']==src4 and b['destination']==dst4 and int(b['available_seats'])>0]
    print(f"  Buses TPJ->MDU with seats: {len(buses)}")
    for b in buses:
        arr_bus = parse_time(b['arrival'])
        dep_bus = parse_time(b['departure'])
        arr_bus_adj = normalize(arr_bus, dep_bus)
        dl_adj = normalize(delayed_eta, dep_bus)
        accepted = arr_bus_adj <= dl_adj
        print(f"    {b['bus_id']} {b['bus_type']} dep={b['departure']} arr={b['arrival']} seats={b['available_seats']} -> accepted={accepted}")
    
    print()
    # Let's also verify threshold exceeded: manualDelay 177 > threshold 15 -> triggers delay mode
    print(f"Manual delay {manual} > threshold 15: {manual > 15} -> delay mode triggered")

print()
print("=" * 70)
print("COMPLETE SUMMARY - EXACT UI INPUTS FOR ALL 4 LEVELS")
print("=" * 70)
