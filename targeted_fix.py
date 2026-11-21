"""
Targeted fixes:
1. Find a true L2: pair with ONLY passenger/local, NO express with seats
2. Fix L3: a route with exactly 1 train serving it (so excluding the booked train = 0 alts)
   AND that hub path exists
3. Fix L4: higher manual delay to push out those 3 remaining express alts
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
print("LEVEL 2 FIX: Finding routes with ZERO express/superfast trains with seats")
print("=" * 70)
# We need a pair where: express trains either don't serve it, OR all have 0 seats
# Let's scan all junction pairs for routes with locals but no express with seats
junction_codes = [s['station_code'] for s in stations_data if s['is_junction'].lower() == 'true']
good_l2 = []
for src in junction_codes:
    for dst in junction_codes:
        if src == dst: continue
        exp = find_direct(src, dst, EXPRESS_TYPES, day='Mon', tclass='2S')
        loc = find_direct(src, dst, LOCAL_TYPES, day='Mon', tclass='2S')
        if not exp and loc:
            good_l2.append((src, dst, loc))

print(f"Found {len(good_l2)} junction pairs with local-only service (no express with seats) on Mon/2S:")
for src, dst, trains in good_l2[:15]:
    sname = station_map[src]['station_name']
    dname = station_map[dst]['station_name']
    # Check if a booked train (with delay profile) serves this pair
    booked = None
    for train in trains_data:
        stops = segments_by_train.get(train['train_number'], [])
        si = get_stop_index(stops, src)
        di = get_stop_index(stops, dst)
        if si == -1 or di == -1 or si >= di: continue
        key_d = f"{train['train_number']}:Mon"
        if key_d in delay_index:
            booked = train
            break
    booked_note = f"booked candidate: #{booked['train_number']} {booked['train_name']}" if booked else "NO BOOKED CANDIDATE"
    print(f"  {sname}({src})->{dname}({dst}): {len(trains)} local trains, {booked_note}")

print()
print("=" * 70)
print("LEVEL 2 DEEP: Let's check NCJ->TEN specifically")
print("=" * 70)
src, dst = 'NCJ', 'TEN'
exp = find_direct(src, dst, EXPRESS_TYPES, day='Mon', tclass='2S')
loc = find_direct(src, dst, LOCAL_TYPES, day='Mon', tclass='2S')
exp_sl = find_direct(src, dst, EXPRESS_TYPES, day='Mon', tclass='SL')
loc_sl = find_direct(src, dst, LOCAL_TYPES, day='Mon', tclass='SL')
print(f"NCJ->TEN: 2S: {len(exp)} exp, {len(loc)} loc | SL: {len(exp_sl)} exp, {len(loc_sl)} loc")

# Check what trains serve NCJ->TEN
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'NCJ')
    di = get_stop_index(stops, 'TEN')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'NCJ')
    arr = get_arr_at(stops, 'TEN')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_2s = f"{train['train_number']}:Mon:2S"
    s2s = seats_index.get(key_2s, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    ssl = seats_index.get(key_sl, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_2S={s2s} seats_SL={ssl}")

print()
print("=" * 70)
print("LEVEL 3 FIX: Find pair with EXACTLY 1 train and hub connections")
print("=" * 70)

# MDU->RMM: Only 6 trains, but they're the same express family
# Let's check: if booked = 52621 Rockfort (MDU->RMM), excluding it leaves 5 more!
# We need a pair with only 1 train total

# Try: Check the newly added routes
# 16382: MAS->TBM->CGL->VM->TPJ->MDU->TEN->NCJ->CAPE
# Segments like MDU->CAPE are only on 16382 and 12633/12634
# Let's check: MDU->CAPE
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'MDU')
    di = get_stop_index(stops, 'CAPE')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'MDU')
    arr = get_arr_at(stops, 'CAPE')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    ssl = seats_index.get(key_sl, None)
    print(f"MDU->CAPE: #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={ssl}")

print()
# Check TEN->CAPE
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'TEN')
    di = get_stop_index(stops, 'CAPE')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'TEN')
    arr = get_arr_at(stops, 'CAPE')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    ssl = seats_index.get(key_sl, None)
    print(f"TEN->CAPE: #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={ssl}")

print()
# NCJ->CAPE?
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'NCJ')
    di = get_stop_index(stops, 'CAPE')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'NCJ')
    arr = get_arr_at(stops, 'CAPE')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    ssl = seats_index.get(key_sl, None)
    print(f"NCJ->CAPE: #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={ssl}")

print()
print("=" * 70)
print("Now checking: what is the hub-based path for TEN->CAPE?")
print("=" * 70)
src3, dst3 = 'TEN', 'CAPE'
exp_d = find_direct(src3, dst3, EXPRESS_TYPES, day='Mon', tclass='SL')
loc_d = find_direct(src3, dst3, LOCAL_TYPES, day='Mon', tclass='SL')
print(f"TEN->CAPE direct: {len(exp_d)} express, {len(loc_d)} local with seats Mon/SL")

# Check hub via NCJ
leg1_ncj = find_direct('TEN', 'NCJ', LOCAL_TYPES | EXPRESS_TYPES, day='Mon', tclass='SL')
leg2_ncj_exp = find_direct('NCJ', 'CAPE', EXPRESS_TYPES, day='Mon', tclass='SL')
leg2_ncj_loc = find_direct('NCJ', 'CAPE', LOCAL_TYPES, day='Mon', tclass='SL')
print(f"Via NCJ: TEN->NCJ: {len(leg1_ncj)}, NCJ->CAPE: {len(leg2_ncj_exp)}exp+{len(leg2_ncj_loc)}loc")
if leg1_ncj:
    for t in leg1_ncj[:2]:
        print(f"  TEN->NCJ: #{t['train']['train_number']} {t['train']['train_name']} dep={mins_to_time(t['dep'])} arr={mins_to_time(t['arr'])}")
if leg2_ncj_exp + leg2_ncj_loc:
    for t in (leg2_ncj_exp + leg2_ncj_loc)[:2]:
        print(f"  NCJ->CAPE: #{t['train']['train_number']} {t['train']['train_name']} dep={mins_to_time(t['dep'])} arr={mins_to_time(t['arr'])}")

print()
print("So for L3: book 12633 Kanyakumari Express (TEN->CAPE)")
# But 12633 serves TEN->NCJ->CAPE, so booked train DOES serve TEN->CAPE
# Excluding 12633: what alternatives are on TEN->CAPE?
alts_exp = find_direct('TEN', 'CAPE', EXPRESS_TYPES, day='Mon', tclass='SL', exclude='12633')
alts_loc = find_direct('TEN', 'CAPE', LOCAL_TYPES, day='Mon', tclass='SL', exclude='12633')
print(f"Alternatives TEN->CAPE (excl 12633): {len(alts_exp)} exp, {len(alts_loc)} loc")
# With manual delay so deadline < all remaining express alternatives
# Check all trains on TEN->CAPE
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, 'TEN')
    di = get_stop_index(stops, 'CAPE')
    if si == -1 or di == -1 or si >= di: continue
    dep = get_dep_at(stops, 'TEN')
    arr = get_arr_at(stops, 'CAPE')
    key_d = f"{train['train_number']}:Mon"
    d = delay_index.get(key_d, None)
    key_sl = f"{train['train_number']}:Mon:SL"
    ssl = seats_index.get(key_sl, None)
    print(f"  #{train['train_number']} {train['train_name']} type={train['train_type']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} delay={d} seats_SL={ssl}")

print()
print("=" * 70)
print("LEVEL 4 FIX: TPJ->MDU with higher delay")
print("=" * 70)
booked_l4 = '12635'
src4, dst4 = 'TPJ', 'MDU'
t_stops = segments_by_train.get(booked_l4, [])
arr_b = get_arr_at(t_stops, dst4)
dep_b = get_dep_at(t_stops, src4)

print(f"Booked: 12635 Vaigai Express, TPJ dep={mins_to_time(dep_b)}, MDU arr={mins_to_time(arr_b)}")
print(f"Delay profile Mon: {delay_index.get('12635:Mon', None)}")

# The 3 passing alternatives: what are they and what are their arrival times?
manual = 177
delayed_eta = (arr_b + manual) % (24*60)
print(f"\nWith manual=177: delayedETA={mins_to_time(delayed_eta)}")
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, src4)
    di = get_stop_index(stops, dst4)
    if si == -1 or di == -1 or si >= di: continue
    if train['train_number'] == booked_l4: continue
    dep = get_dep_at(stops, src4)
    arr = get_arr_at(stops, dst4)
    if dep is None or arr is None: continue
    arr_adj = normalize(arr, dep)
    dl_adj = normalize(delayed_eta, dep)
    accepted = arr_adj <= dl_adj
    key_sl = f"{train['train_number']}:Mon:SL"
    ssl = seats_index.get(key_sl, None)
    key_2s = f"{train['train_number']}:Mon:2S"
    s2s = seats_index.get(key_2s, None)
    if ssl and ssl > 0:
        print(f"  #{train['train_number']} {train['train_name']} dep={mins_to_time(dep)} arr={mins_to_time(arr)} arr_adj={arr_adj} dl_adj={dl_adj} accepted={accepted} seats_SL={ssl}")

# Find minimum delay to reject ALL alternatives
all_trains_tpj_mdu = []
for train in trains_data:
    stops = segments_by_train.get(train['train_number'], [])
    si = get_stop_index(stops, src4)
    di = get_stop_index(stops, dst4)
    if si == -1 or di == -1 or si >= di: continue
    if train['train_number'] == booked_l4: continue
    dep = get_dep_at(stops, src4)
    arr = get_arr_at(stops, dst4)
    if dep is None or arr is None: continue
    key_sl = f"{train['train_number']}:Mon:SL"
    ssl = seats_index.get(key_sl, None)
    if ssl and ssl > 0:
        all_trains_tpj_mdu.append({'train': train, 'dep': dep, 'arr': arr})

print(f"\nAll alternative trains TPJ->MDU with SL seats: {len(all_trains_tpj_mdu)}")
# For each, find the deadline that would REJECT it: deadline < arr (plain clock comparison)
# So deadline must be < minimum arr of all alternatives
arr_times = [t['arr'] for t in all_trains_tpj_mdu]
print(f"Arrival times: {[mins_to_time(a) for a in sorted(arr_times)]}")
min_arr = min(arr_times)
print(f"Min arrival: {mins_to_time(min_arr)} = {min_arr} min")
# Need delayedETA < min_arr
# delayedETA = arr_b + manual_delay (wraps if > 1440)
# We need: (arr_b + manual) % 1440 < min_arr? No wait...
# The actual check is: normalize(arr, dep) > normalize(deadline, dep) -> REJECT
# Let me be precise: for each train, it's rejected when arr_adj > dl_adj
# arr_adj = normalize(arr, dep) and dl_adj = normalize(deadline, dep)
# deadline = (arr_b + manual) -- THIS CAN EXCEED 1440 without wrapping in the JS code!
# In JS: delayedEta = scheduledArr + effectiveDelay (no modulo, just adds)
# So deadline is NOT wrapped -- it can be e.g. 1269 + 400 = 1669

print()
print("CRITICAL: In JS code, delayedEta = scheduledArr + effectiveDelay (no mod, can exceed 1440)")
print("So deadline can be > 1440, meaning it refers to a time 'next day'")
print()
# arr_b = 21:09 = 1269 mins
# For deadline to reject a train arriving at e.g. 23:59 = 1439:
# Train: dep=18:15=1095, arr=23:59=1439
# arr_adj = normalize(1439, 1095) = 1439 (>1095, no wrap)
# deadline = 1269 + manual
# dl_adj = normalize(1269+manual, 1095)
# If 1269+manual >= 1095 (always true for positive manual): dl_adj = 1269+manual
# Rejected if: 1439 > 1269+manual => manual < 170
# So train arriving 23:59 is rejected if manual < 170!

# That means with manual=170, trains arriving after 21:09+170=00:09 (1439 min) get rejected
# Wait: 1269 + 170 = 1439 = 23:59. Trains arriving at 23:59 exactly: arr_adj=1439, dl_adj=1439 -> accepted
# With manual=171: dl=1440, dl_adj=normalize(1440,1095)=1440, arr_adj=1439 -> 1439<=1440 -> still accepted!

# Let me find what manual delay value rejects ALL trains
# For each train (dep=D, arr=A): rejected if normalize(A, D) > normalize(deadline, D)
# = A >= D: A > deadline -> rejected if deadline < A -> manual < A - arr_b
# = A < D (overnight): A+1440 > normalize(deadline,D) -> deadline+1440 if deadline<D -> A+1440>deadline+1440->A>deadline->same

# Actually it's cleaner: the train IS rejected if arr_adj > dl_adj
# For non-overnight trains (A >= D): arr_adj = A, dl_adj = max(deadline, deadline+1440 if deadline<D)
# Most interesting: if deadline >= D (booked train arr + manual >= alt train departure):
#   dl_adj = deadline (no wrap)
#   Rejected if A > deadline, i.e., alt arr > (booked arr + manual)

print("For non-overnight alternative trains:")
for t in all_trains_tpj_mdu:
    D = t['dep']
    A = t['arr']
    if A >= D:  # non-overnight
        # Rejected if A > deadline = arr_b + manual
        # i.e., manual < A - arr_b
        min_manual = A - arr_b
        print(f"  #{t['train']['train_number']} {t['train']['train_name']}: dep={mins_to_time(D)}, arr={mins_to_time(A)} -> rejected if manual < {min_manual} (i.e. deadline < {mins_to_time(A)})")
    else:  # overnight
        # arr_adj = A + 1440, dl_adj = deadline if deadline >= D else deadline + 1440
        # If deadline >= D: dl_adj=deadline, rejected if A+1440 > deadline -> manual > A+1440-arr_b-1
        # (since deadline=arr_b+manual, and we need deadline < A+1440: manual < A+1440-arr_b)
        min_manual = A + 1440 - arr_b
        print(f"  #{t['train']['train_number']} {t['train']['train_name']}: dep={mins_to_time(D)}, arr={mins_to_time(A)} (overnight) -> rejected if manual >= {min_manual} ({mins_to_time(A+1440)})")

print()
# Find the threshold: max of "min manual to reject each non-overnight" = the highest A among non-overnight trains
# For overnight trains: we need manual >= A+1440-arr_b which is usually very large
non_overnight = [(t['arr'], t) for t in all_trains_tpj_mdu if t['arr'] >= t['dep']]
overnight = [(t['arr'], t) for t in all_trains_tpj_mdu if t['arr'] < t['dep']]
print(f"Non-overnight alternatives: {len(non_overnight)}")
print(f"Overnight alternatives: {len(overnight)}")
if non_overnight:
    max_non_overnight_arr = max(a for a,t in non_overnight)
    print(f"  Latest non-overnight arrival: {mins_to_time(max_non_overnight_arr)}")
    print(f"  Manual needed to reject all non-overnight: > {max_non_overnight_arr - arr_b}")
if overnight:
    for a, t in overnight:
        print(f"  Overnight: #{t['train']['train_number']} arr={mins_to_time(a)} -> need manual >= {a+1440-arr_b}")
