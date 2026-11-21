import csv

# Load stations
stations = {}
with open('data/stations.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        stations[row['station_code']] = row['station_name']

# Load segments to find which station codes appear in actual routes
seg_codes = set()
with open('data/segments.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        seg_codes.add(row['station_code'])

# Load trains to find which stations are used as source/dest
train_codes = set()
with open('data/trains.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        train_codes.add(row['source_station'])
        train_codes.add(row['destination_station'])

reachable = seg_codes | train_codes

# Target stations to audit
targets = {
    'Rameswaram': ['RMM'],
    'Karaikudi': ['KKDI'],
    'Sivaganga': ['SVG'],
    'Dindigul': ['DG'],
    'Erode': ['ED'],
    'Tiruppur': ['TP', 'TUP'],
    'Karur': ['KRR'],
    'Vellore': ['VLR'],
    'Katpadi': ['KPD'],
    'Villupuram': ['VM'],
    'Cuddalore': ['CDM', 'CUPJ'],
    'Thanjavur': ['TJ'],
    'Kumbakonam': ['KMU'],
    'Mayiladuthurai': ['MV'],
    'Tirunelveli': ['TEN'],
    'Thoothukudi': ['TN'],
}

print('=== STATION AUDIT ===')
for name, codes in targets.items():
    found_codes = [c for c in codes if c in stations]
    if not found_codes:
        print(f'{name}: MISSING from stations.csv')
    else:
        code = found_codes[0]
        in_seg = any(c in seg_codes for c in codes)
        in_train = any(c in train_codes for c in codes)
        if in_seg or in_train:
            # Count trains it appears in
            count = sum(1 for c in codes if c in seg_codes)
            trains_list = []
            with open('data/segments.csv', encoding='utf-8') as f:
                t_set = set(r['train_number'] for r in csv.DictReader(f) if r['station_code'] in codes)
            with open('data/trains.csv', encoding='utf-8') as f:
                t2 = set()
                for r in csv.DictReader(f):
                    if r['source_station'] in codes or r['destination_station'] in codes:
                        t2.add(r['train_number'])
            all_trains = t_set | t2
            print(f'{name} ({", ".join(found_codes)}): PRESENT - REACHABLE via {len(all_trains)} train(s)')
        else:
            print(f'{name} ({", ".join(found_codes)}): PRESENT - ISOLATED (in CSV but not in any route segment)')

print()
print('=== CAPE (Kanniyakumari) COVERAGE ===')
cape_in_stations = 'CAPE' in stations
print(f'CAPE in stations.csv: {cape_in_stations}')

with open('data/trains.csv', encoding='utf-8') as f:
    cape_trains_list = [r['train_name'] + ' (' + r['train_number'] + ')' for r in csv.DictReader(f)
                        if r['source_station'] == 'CAPE' or r['destination_station'] == 'CAPE']
print(f'Trains with CAPE as source/dest: {cape_trains_list}')

with open('data/segments.csv', encoding='utf-8') as f:
    cape_seg_trains = set(r['train_number'] for r in csv.DictReader(f) if r['station_code'] == 'CAPE')
print(f'Trains with CAPE as intermediate stop (segments): {cape_seg_trains}')

all_cape_trains = set(t.split('(')[1].rstrip(')') for t in cape_trains_list) | cape_seg_trains
print(f'Total trains serving CAPE: {len(all_cape_trains)}')

print()
print('=== NCJ / Nagercoil COVERAGE ===')
ncj_codes = ['NCJ']
with open('data/segments.csv', encoding='utf-8') as f:
    ncj_trains = set(r['train_number'] for r in csv.DictReader(f) if r['station_code'] == 'NCJ')
with open('data/trains.csv', encoding='utf-8') as f:
    ncj_trains2 = set(r['train_number'] for r in csv.DictReader(f)
                      if r['source_station'] == 'NCJ' or r['destination_station'] == 'NCJ')
print(f'Trains serving NCJ: {len(ncj_trains | ncj_trains2)} total')
print(f'  As source/dest: {ncj_trains2}')
print(f'  As intermediate stop: {ncj_trains}')
