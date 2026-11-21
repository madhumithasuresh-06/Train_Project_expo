"""
Targeted deep-dive for L2, L3, L4 exact scenarios.
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
bus_data = load_csv('data/bus_routes.csv')
delay_data = load_csv('data/delay_profile.csv')

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

def find_direct_trains(src, dst, types, deadline=None, day='Mon', tclass='SL', exclude=None):
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
        arr_adj = normalize(arr, dep)
        if deadline is not None:
            dl_adj = normalize(deadline, dep)
            if arr_adj > dl_adj: continue
        key = f"{train['train_number']}:{day}:{tclass}"
        seats = seats_index.get(key, None)
        if seats is None or seats <= 0: continue
        results.append({'train': train, 'dep': dep, 'arr': arr, 'seats': seats})
    return results

print("=" * 70)
print("LEVEL 2 DEEP DIVE")
print("=" * 70)
# KKDI->TPJ has good local trains (Karaikkudi Passenger series)
# Let's confirm exactly
src, dst = 'KKDI', 'TPJ'
exp = find_direct_trains(src, dst, EXPRESS_TYPES, day='Mon', tclass='SL')
loc = find_direct_trains(src, dst, LOCAL_TYPES, day='Mon', tclass='SL')
print(f"KKDI->TPJ: {len(exp)} express, {len(loc)} local trains with seats on Mon/SL")
for t in loc[:3]:
    d = delay_index.get(f"{t['train']['train_number']}:Mon", None)
    print(f"  {t['train']['train_name']} #{t['train']['train_number']} type={t['train']['train_type']}")
    print(f"    dep KKDI={mins_to_time(t['dep'])} arr TPJ={mins_to_time(t['arr'])} seats={t['seats']} delay_profile={d}")

# The booked train needs to be one of these locals, with a delay profile
# So: user books one of the Karaikkudi Passengers, enters delay > threshold -> L2 alternatives
# Actually wait: the BOOKED train is what the user is ON. The alternatives are what the system finds.
# So for L2, we need:
#   - booked train can be ANYTHING serving KKDI->TPJ
#   - the alternatives = only local trains (no express between KKDI->TPJ)
# The booked train itself just needs a delay profile (or manual delay)

print()
# What trains serve KKDI and have delay profiles?
print("Trains serving KKDI->TPJ with delay profile on Monday:")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'KKDI')
    di = get_stop_index(stops, 'TPJ')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'KKDI')
    arr = get_arr_at(stops, 'TPJ')
    key_delay = f"{train['train_number']}:Mon"
    d = delay_index.get(key_delay, None)
    key_seat = f"{train['train_number']}:Mon:SL"
    seats = seats_index.get(key_seat, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={seats}")

print()
print("=" * 70)
print("LEVEL 3 DEEP DIVE: KKDI->TJ (Karaikudi -> Thanjavur)")
print("=" * 70)
# Verify no direct trains
src, dst = 'KKDI', 'TJ'
exp = find_direct_trains(src, dst, EXPRESS_TYPES, day='Mon', tclass='SL')
loc = find_direct_trains(src, dst, LOCAL_TYPES, day='Mon', tclass='SL')
print(f"KKDI->TJ direct: {len(exp)} express, {len(loc)} local")

# Hub connections: what hubs connect KKDI to TJ?
# TPJ is a major junction between them!
# KKDI->TPJ (via Karaikkudi Passengers) + TPJ->TJ (via various trains)
hub = 'TPJ'
leg1 = find_direct_trains('KKDI', hub, LOCAL_TYPES, day='Mon', tclass='SL')
leg2_exp = find_direct_trains(hub, 'TJ', EXPRESS_TYPES, day='Mon', tclass='SL')
leg2_loc = find_direct_trains(hub, 'TJ', LOCAL_TYPES, day='Mon', tclass='SL')
print(f"\nHub TPJ: KKDI->TPJ: {len(leg1)} local trains, TPJ->TJ: {len(leg2_exp)} express + {len(leg2_loc)} local")
if leg1 and (leg2_exp or leg2_loc):
    l1 = leg1[0]
    l2 = (leg2_exp or leg2_loc)[0]
    l1_arr = normalize(l1['arr'], l1['dep'])
    l2_dep = normalize(l2['dep'], l1['dep'])
    buffer_ok = l2_dep - l1_arr >= 15
    print(f"  Leg1: {l1['train']['train_name']} dep={mins_to_time(l1['dep'])} arr={mins_to_time(l1['arr'])}")
    print(f"  Leg2: {l2['train']['train_name']} dep={mins_to_time(l2['dep'])} arr={mins_to_time(l2['arr'])}")
    print(f"  Transfer buffer >= 15 min: {buffer_ok} (l1_arr={l1_arr}, l2_dep={l2_dep}, diff={l2_dep-l1_arr})")

# What booked train to use for L3 test?
# The booked train must serve KKDI and TPJ... but we need src=KKDI, dst=TJ
# The booked train must serve KKDI->TJ... but there are no trains that do!
# The API requires trainMap[trainNumber] and the stops to include src and dst
# Looking at recommendation.js line 302-306:
# srcIdx = getStopIndex(bookedStops, sourceStation)
# dstIdx = getStopIndex(bookedStops, destinationStation)
# if srcIdx == -1 or dstIdx == -1: error
# So the BOOKED train must serve KKDI->TJ which doesn't exist!
# That's a problem. Let's check what the UI actually shows for available trains when src=KKDI, dst=TJ
print()
print("Trains with both KKDI and TJ as stops (any order):")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    codes = [s['station_code'] for s in stops]
    if 'KKDI' in codes and 'TJ' in codes:
        ki = get_stop_index(stops, 'KKDI')
        ti = get_stop_index(stops, 'TJ')
        print(f"  #{train['train_number']} {train['train_name']}: KKDI=stop{ki}, TJ=stop{ti}, direction={'KKDI->TJ' if ki < ti else 'TJ->KKDI'}")

print()
print("So for L3, we need a pair where the BOOKED train also has both stops!")
print("This means L3 test needs: booked train serves src->dst, alternatives don't exist directly,")
print("but hub path exists. Let's find such a case...")
print()

# Find pairs where:
# 1. A train covers src->dst (so user CAN be booked on it)
# 2. No OTHER express trains cover src->dst as alternatives
# 3. No local trains cover src->dst as alternatives (without the booked train)
# 4. But hub connections exist

# Let's look for long-distance trains that go through many stations
# If booked train is the ONLY train doing src->dst, then alternatives via L1/L2 = 0, falls to L3

# Find pairs where EXACTLY ONE train serves src->dst
train_pair_count = {}
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    for i, s1 in enumerate(stops):
        for j, s2 in enumerate(stops):
            if j <= i: continue
            pair = (s1['station_code'], s2['station_code'])
            if pair not in train_pair_count:
                train_pair_count[pair] = []
            train_pair_count[pair].append(train['train_number'])

# Find pairs with seats that have only 1 train (or where removing booked train leaves 0)
print("Pairs with seats on Mon/SL served by exactly 1 train (ideal for L3):")
single_train_pairs = []
for (src, dst), train_nums in train_pair_count.items():
    # Check if any of these trains have seats on Mon/SL
    trains_with_seats = []
    for tn in train_nums:
        key = f"{tn}:Mon:SL"
        s = seats_index.get(key, None)
        if s and s > 0:
            trains_with_seats.append(tn)
    if len(trains_with_seats) == 1:
        tn = trains_with_seats[0]
        t = train_map.get(tn, {})
        # Check that src and dst are both in stationmap
        if src in station_map and dst in station_map:
            src_name = station_map[src]['station_name']
            dst_name = station_map[dst]['station_name']
            single_train_pairs.append((src, dst, tn, t.get('train_name',''), t.get('train_type','')))

# Filter to only junction stations for interesting results
junction_codes = {s['station_code'] for s in stations_data if s['is_junction'].lower() == 'true'}
interesting = [(s,d,tn,nm,tp) for s,d,tn,nm,tp in single_train_pairs 
               if s in junction_codes and d in junction_codes and s != d]
interesting.sort(key=lambda x: x[3])
print(f"Found {len(interesting)} junction->junction pairs with exactly 1 train:")
for s,d,tn,nm,tp in interesting[:20]:
    sn = station_map[s]['station_name']
    dn = station_map[d]['station_name']
    print(f"  {sn}({s})->{dn}({d}): #{tn} {nm} ({tp})")

print()
print("=" * 70)
print("LEVEL 4 PRECISE CALCULATION: MAS->MDU")
print("=" * 70)
# For L4, user is booked on a train, enters enough manual delay
# so that delayedETA > all alternative arrivals
# Best candidate: use a train with a delay profile, then verify with manualDelay

# Best booked train for MAS->MDU: something like 12635 Vaigai Express (MS->MDU)
# But let's check trains that go MAS->MDU specifically
print("Trains serving MAS->MDU:")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'MAS')
    di = get_stop_index(stops, 'MDU')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'MAS')
    arr = get_arr_at(stops, 'MDU')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_s = f"{train['train_number']}:Mon:SL"
    seats = seats_index.get(key_s, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={seats}")

print()
print("For L4, booked = 12633 Kanyakumari Express (MAS->MDU->..->CAPE)")
t12633 = segments_by_train.get('12633', [])
mas_i = get_stop_index(t12633, 'MAS')
mdu_i = get_stop_index(t12633, 'MDU')
if mas_i != -1 and mdu_i != -1:
    dep_mas = get_dep_at(t12633, 'MAS')
    arr_mdu = get_arr_at(t12633, 'MDU')
    print(f"  12633 dep MAS={mins_to_time(dep_mas)}, arr MDU={mins_to_time(arr_mdu)}")
    print(f"  Delay profile: {delay_index.get('12633:Mon', 'MISSING')}")
    
    # Find all alternative trains MAS->MDU (excluding 12633)
    all_alts = find_direct_trains('MAS', 'MDU', EXPRESS_TYPES | LOCAL_TYPES, day='Mon', tclass='SL', exclude='12633')
    print(f"  Alternative trains MAS->MDU: {len(all_alts)}")
    for t in sorted(all_alts, key=lambda x: normalize(x['arr'], dep_mas)):
        arr_n = normalize(t['arr'], dep_mas)
        print(f"    {t['train']['train_name']} #{t['train']['train_number']} arr={mins_to_time(t['arr'])} (norm={arr_n})")
    
    if all_alts:
        max_arr_n = max(normalize(t['arr'], dep_mas) for t in all_alts)
        # delayedETA = arr_mdu + manualDelay
        # We need delayedETA_normalized_to_dep_mas > max_arr_n
        # normalize(arr_mdu + delay, dep_mas) > max_arr_n
        # arr_mdu + delay might wrap around midnight
        # Let's just try: manualDelay = max_arr_n - arr_mdu + 1
        # But arr_mdu = 01:25 = 85 mins, dep_mas = 17:20 = 1040
        # normalize(85, 1040) = 85+1440 = 1525
        # normalize(delayedETA, 1040) where delayedETA = 85 + manualDelay
        # We want this > max_arr_n
        arr_mdu_n = normalize(arr_mdu, dep_mas)
        print(f"\n  arr_mdu normalized = {arr_mdu_n} ({mins_to_time(arr_mdu_n % (24*60))})")
        print(f"  max_arr_n of alternatives = {max_arr_n} ({mins_to_time(max_arr_n % (24*60))})")
        # We want: normalize(arr_mdu + delay, dep_mas) > max_arr_n
        # = arr_mdu + delay (if >= dep_mas) OR arr_mdu + delay + 1440 (if < dep_mas)
        # arr_mdu = 85, delay makes it: 85 + delay
        # For this to be >= dep_mas(1040): 85 + delay >= 1040 -> delay >= 955 (too large)
        # So: normalize(85+delay, 1040) = 85 + delay + 1440 = delay + 1525
        # We want delay + 1525 > max_arr_n
        # delay > max_arr_n - 1525
        needed = max_arr_n - arr_mdu_n + 1
        print(f"  Minimum manualDelay to push ALL alternatives past deadline: {needed} min")
        print(f"  That gives delayedETA = {mins_to_time((arr_mdu + needed) % (24*60))}")
        print(f"  With threshold=15, user needs to enter manualDelay={max(16, needed)} min")
        
        # Verify buses exist for MAS->MDU
        buses = [b for b in bus_data if b['source']=='MAS' and b['destination']=='MDU' and int(b['available_seats'])>0]
        print(f"\n  Buses MAS->MDU with seats: {len(buses)}")
        for b in buses:
            print(f"    {b['bus_id']} {b['bus_type']} dep={b['departure']} arr={b['arrival']} seats={b['available_seats']}")

print()
print("=" * 70)
print("VERIFY: MAS->MDU L4 with smaller delay - pick a train that departs LATE")  
print("so alternatives departing earlier all already left")
print("=" * 70)
# Actually, the deadline filter is on ARRIVAL not DEPARTURE
# So what we need is: delayedETA < all alternative ARRIVALS
# If all alternatives arrive VERY LATE (after our delayed ETA), they get accepted... wrong
# Re-read: if arrAdj > deadlineAdj: SKIP (arr too late, rejected)
# So we WANT train arrivals to be LATER than our deadline (so they get rejected)
# delayedETA must be SMALL (early in the day), making all alternatives' arrivals > it
# Actually NO -- if deadline is 03:24 and alternative arrives at 14:00, 
# normalize(14:00, dep) where dep is alt's own departure, not booked dep
# That's the bug in my analysis -- each train normalizes relative to ITS OWN departure!

print()
print("Re-reading code: normalizeComparison in findDirectTrains uses dep as reference per-train")
print("So each train's arrival is normalized relative to its OWN departure, not booked train's dep")
print("deadlineAdj = normalize(deadlineMinutes, depMin) where depMin is THAT TRAIN's departure")
print()
print("This means: for each alternative train T with dep=D, arr=A:")
print("  arr_adj = A if A>=D else A+1440")
print("  deadline_adj = deadline if deadline>=D else deadline+1440")
print("  train accepted if arr_adj <= deadline_adj")
print("  i.e., if deadline >= A (or wraps around)")
print()
print("So if deadline = 03:24, and alt train departs at 04:00 and arrives at 15:00:")
print("  arr_adj = normalize(900, 240) = 900")
print("  deadline_adj = normalize(204, 240) = 204+1440 = 1644")  
print("  900 <= 1644 -> ACCEPTED! (The train that departs at 04:00 and arrives 15:00 IS accepted)")
print()
print("This means a late deadline is MORE permissive, not less!")
print("For L4, we need deadline to be VERY EARLY so that alternatives are 'too late'")
print("i.e., their arrival (normalized to their own dep) > deadline (normalized to their dep)")
print()
print("Simplest case: deadline very early morning, trains arrive in the afternoon/evening")
print("e.g., deadline = 06:00 = 360 min")
print("  Alt departs 08:00 (480), arrives 18:00 (1080):")
print("    arr_adj = normalize(1080, 480) = 1080")
print("    deadline_adj = normalize(360, 480) = 360+1440 = 1800")
print("    1080 <= 1800 -> accepted")
print()
print("Hmm still accepted. The deadline wraps forward too.")
print("The ONLY way arr_adj > deadline_adj is if train takes longer than deadline from its dep")
print("i.e., train arrives AFTER the deadline when counting from its own departure")
print()
print("So: deadline must be BEFORE the train's arrival, when counting from that train's dep")
print("normalize(arr, dep) > normalize(deadline, dep)")
print("=> arr-dep > deadline-dep (both positive) => arr > deadline")
print("=> or if arr wraps, arr+1440-dep > deadline-dep => arr+1440 > deadline")
print()
print("So effectively: arr_adj > deadline means the train arrives AFTER the deadline (24h clock)")
print("Simple case: deadline = 08:00, train arrives at 18:00 -> 18:00 > 08:00 -> REJECTED!")
print("deadline = 08:00, train arrives at 07:00 -> arr_adj=7*60=420, dl_adj=normalize(480,dep)")
print()
print("Let's verify with MAS->CBE:")
print("All alts for MAS->CBE with their arrivals:")
alts_mas_cbe = find_direct_trains('MAS', 'CBE', EXPRESS_TYPES, day='Mon', tclass='SL')
for t in alts_mas_cbe:
    print(f"  {t['train']['train_name']} dep={mins_to_time(t['dep'])} arr={mins_to_time(t['arr'])}")

print()
print("If deadline = say 200 (03:20 AM), most trains that depart morning and arrive evening")
print("would have arr_adj > deadline_adj? Let's check Kovai dep=11:45=705, arr=21:49=1309")
dep_kovai = 705  # 11:45
arr_kovai = 1309  # 21:49
dl = 200  # 03:20
arr_adj = normalize(arr_kovai, dep_kovai)  # 1309 >= 705, so 1309
dl_adj = normalize(dl, dep_kovai)  # 200 < 705, so 200+1440=1640
print(f"  Kovai: arr_adj={arr_adj}, dl_adj={dl_adj}, accepted={arr_adj <= dl_adj} -> {'YES' if arr_adj <= dl_adj else 'NO'}")

# What about Rockfort dep=15:45=945, arr=22:11=1331?
dep_rock = 945; arr_rock = 1331
arr_adj_r = normalize(arr_rock, dep_rock)  # 1331
dl_adj_r = normalize(dl, dep_rock)  # 200+1440=1640
print(f"  Rockfort: arr_adj={arr_adj_r}, dl_adj={dl_adj_r}, accepted={arr_adj_r <= dl_adj_r}")

print()
print("Conclusion: even with deadline=200, trains are still accepted because")
print("normalize wraps deadline forward making it 1640, and arr=1309 < 1640")
print()
print("The ONLY way to reject trains is: arr_adj > dl_adj")
print("i.e., arr > dl when train runs within same day, OR")
print("when the train is an overnight train where arr wraps to next day")
print()
print("Actually let me re-read more carefully:")
print("normalizeComparison(value, reference): if value < reference, return value+1440")
print("So if deadline=200 and dep=1040 (booked dep):")
print("  deadlineAdj relative to booked dep = normalize(200, 1040) = 200+1440=1640")
print("But in findDirectTrains, dep=depMin is EACH ALTERNATIVE's departure!")
print()
print("Let's try: what if deadline is VERY early, say 60 (01:00 AM)?")
dl2 = 60
for t in alts_mas_cbe:
    dep = t['dep']
    arr = t['arr']
    arr_adj = normalize(arr, dep)
    dl_adj = normalize(dl2, dep)
    accepted = arr_adj <= dl_adj
    print(f"  {t['train']['train_name']}: dep={mins_to_time(dep)}, arr={mins_to_time(arr)}, arr_adj={arr_adj}, dl_adj={dl_adj}, accepted={accepted}")

print()
print("KEY INSIGHT: For L4, we need very early deadline so dl_adj < arr_adj")
print("This means: deadline < dep of every alternative train (so dl gets +1440)")
print("Then: dl_adj = deadline+1440, arr_adj = arr (already >= dep)")  
print("Accepted if: arr <= deadline+1440, i.e., arr - deadline <= 1440 (always true...)")
print()
print("ACTUALLY: The train IS rejected when arr_adj > dl_adj")
print("arr_adj > dl_adj means:")
print("  If deadline >= dep: arr >= dep (so arr_adj=arr), dl_adj=deadline => rejected if arr > deadline")
print("  If deadline < dep: arr_adj = arr (if arr>=dep) or arr+1440, dl_adj = deadline+1440")
print("    If arr>=dep: arr > deadline+1440? Only if arr > deadline+1440 which can't happen in 24h")  
print("    If arr<dep (overnight): arr+1440 > deadline+1440 => arr > deadline")
print()
print("So: an alternative train is REJECTED if its ARRIVAL TIME (in plain 24h) > deadline (in plain 24h)")
print("EXCEPT if the train is an overnight train (arr < dep), in which case it's arr > deadline")
print("But even overnight: arr > deadline iff arrival (wrapped) > deadline")
print()
print("Simplified: the engine essentially checks if the arrival time (in clock time) > deadline (clock time)")
print("For non-overnight trains: arr > deadline -> rejected")
print("For overnight trains: the arr wraps but... let me just test with numbers")
print()
print("CLEAN EXAMPLE for L4:")
print("If booked train: 12633 MAS->MDU, dep=17:20, arr_MDU=01:25 (next day)")
print("delayedETA = 01:25 + manualDelay")
print("For deadline to be say 04:00=240:")
print("  Alternative: dep=17:20(1040), arr=15:00(900) -- Brindavan Express MAS->MDU?")
# Check 12639 Brindavan MAS->MDU
t12639 = segments_by_train.get('12639', [])
mas_i = get_stop_index(t12639, 'MAS')
mdu_i = get_stop_index(t12639, 'MDU')
if mas_i != -1:
    print(f"  12639 stops: {[s['station_code'] for s in t12639]}")
else:
    print("  12639 does not serve MAS->MDU directly")

print()
print("Let me find ALL pairs (src, dst) where:")
print("1. Bus exists with seats")
print("2. Few trains exist (easier to exceed deadline)")
print("3. A booked train has delay profile")

bus_pairs_with_seats = {}
for b in bus_data:
    if int(b['available_seats']) > 0:
        pair = (b['source'], b['destination'])
        if pair not in bus_pairs_with_seats:
            bus_pairs_with_seats[pair] = []
        bus_pairs_with_seats[pair].append(b)

print("\nFor each bus pair, counting trains that serve it:")
for (src, dst), buses in bus_pairs_with_seats.items():
    trains_serving = []
    for train in trains_data:
        stops = segments_by_train.get(train['train_number'], [])
        si = get_stop_index(stops, src)
        di = get_stop_index(stops, dst)
        if si == -1 or di == -1 or si >= di: continue
        dep = get_dep_at(stops, src)
        arr = get_arr_at(stops, dst)
        key_s = f"{train['train_number']}:Mon:SL"
        seats = seats_index.get(key_s, None)
        key_d = f"{train['train_number']}:Mon"
        has_delay = key_d in delay_index
        if dep and arr and seats and seats > 0:
            trains_serving.append({'train': train, 'dep': dep, 'arr': arr, 'seats': seats, 'has_delay': has_delay})
    
    booked_candidates = [t for t in trains_serving if t['has_delay']]
    print(f"  {src}->{dst}: {len(trains_serving)} trains with seats, {len(booked_candidates)} with delay profile")
    if booked_candidates:
        for t in booked_candidates[:2]:
            print(f"    Booked candidate: #{t['train']['train_number']} {t['train']['train_name']} type={t['train']['train_type']} dep={mins_to_time(t['dep'])} arr={mins_to_time(t['arr'])}")
        # Find the latest arriving train (the one we need to beat)
        if trains_serving:
            # For each train, compute: what deadline makes this train rejected?
            # rejected if: normalize(arr, dep) > normalize(deadline, dep)
            # = arr >= dep (non-overnight): arr > deadline -> deadline must be < arr
            # = arr < dep (overnight): arr+1440 > deadline+1440 only if arr > deadline -> same!
            # So: train rejected if deadline (clock) < arr (clock) - but for overnight, arr is e.g. 01:25
            # and deadline < 01:25 would reject it if deadline < 85
            # Let's find the minimum deadline that would reject ALL alternative trains
            # = minimum of all alternative arrival times
            alts_only = [t for t in trains_serving if t['train']['train_number'] != booked_candidates[0]['train']['train_number']]
            if alts_only:
                arr_times = [t['arr'] for t in alts_only]
                min_arr = min(arr_times)
                # To reject this train: deadline < min_arr
                # So set deadline = min_arr - 1
                needed_eta = min_arr - 1
                booked = booked_candidates[0]
                # delayedETA = arr_booked + manualDelay = needed_eta
                needed_delay = needed_eta - booked['arr']
                if needed_delay < 0: needed_delay += 1440  # wrap
                # Also must exceed threshold (15)
                actual_delay = max(16, needed_delay)
                print(f"    To reject all alts (min alt arr={mins_to_time(min_arr)}), need deadline<{mins_to_time(min_arr)}")
                print(f"    Booked arr={mins_to_time(booked['arr'])}, needed manualDelay={actual_delay} min")
                print(f"    This gives delayedETA={mins_to_time((booked['arr']+actual_delay)%1440)}")
                # But we need threshold to be less than delay for it to trigger at all
                print(f"    Use threshold=15, manualDelay={actual_delay}")
                # Verify buses
                print(f"    Buses available: {len(buses)}")
                for b in buses[:2]:
                    print(f"      {b['bus_id']} {b['bus_type']} dep={b['departure']} seats={b['available_seats']}")
