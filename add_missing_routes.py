import csv

# We need to add more trains to serve SVG (Sivaganga) and TN (Thoothukudi)
# both of which only have 1 train each.
# Also need to ensure CAPE is fine (already has 2).
# We'll add:
# 1. Return train for 12636 (KKDI->MDU via SVG)  -- already SVG is en-route
# 2. A second pair of trains: MAS->KKDI via MDU, SVG (Sivaganga Express)
# 3. Return train for 12638 (TN->MDU)
# 4. Second pair: MAS->TN via MDU (Pearl City Express, already a used name -- use new name)
# 5. A third CAPE train via different route (MAS->CAPE via different stops) for diversity

new_trains = [
    # Return of 12636: KKDI->MDU via SVG
    {'train_number': '12642', 'train_name': 'Sivaganga Passenger Return', 'train_type': 'passenger',
     'source_station': 'KKDI', 'destination_station': 'MDU', 'days_of_operation': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'},
    # A second MAS->KKDI via SVG (express)
    {'train_number': '22636', 'train_name': 'Sivaganga Express', 'train_type': 'express',
     'source_station': 'MAS', 'destination_station': 'KKDI', 'days_of_operation': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'},
    {'train_number': '22637', 'train_name': 'Sivaganga Express Return', 'train_type': 'express',
     'source_station': 'KKDI', 'destination_station': 'MAS', 'days_of_operation': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'},
    # Return of 12638: TN->MDU
    {'train_number': '12639', 'train_name': 'Thoothukudi Express Return', 'train_type': 'express',
     'source_station': 'TN', 'destination_station': 'MDU', 'days_of_operation': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'},
    # Second pair for TN: MAS->TN via MDU (Tuticorin Mail)
    {'train_number': '16732', 'train_name': 'Tuticorin Mail', 'train_type': 'superfast',
     'source_station': 'MAS', 'destination_station': 'TN', 'days_of_operation': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'},
    {'train_number': '16733', 'train_name': 'Tuticorin Mail Return', 'train_type': 'superfast',
     'source_station': 'TN', 'destination_station': 'MAS', 'days_of_operation': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun'},
    # Third CAPE train: via TVC (Thiruvananthapuram) -- different route approach
    {'train_number': '16382', 'train_name': 'Cape Korail Express', 'train_type': 'express',
     'source_station': 'MAS', 'destination_station': 'CAPE', 'days_of_operation': 'Mon,Wed,Fri,Sun'},
    {'train_number': '16381', 'train_name': 'Cape Korail Express Return', 'train_type': 'express',
     'source_station': 'CAPE', 'destination_station': 'MAS', 'days_of_operation': 'Tue,Thu,Sat'},
]

# Segments for new trains
# 12642: KKDI -> SVG -> MDU (return of 12636)
# 22636: MAS -> MDU -> SVG -> KKDI
# 22637: KKDI -> SVG -> MDU -> MAS
# 12639: TN -> MDU (return of 12638)
# 16732: MAS -> TBM -> CGL -> VM -> TPJ -> MDU -> TN (via TVP)
# 16733: TN -> MDU -> TPJ -> VM -> CGL -> TBM -> MAS
# 16382: MAS -> TBM -> CGL -> VM -> TPJ -> MDU -> TEN -> NCJ -> CAPE
# 16381: CAPE -> NCJ -> TEN -> MDU -> TPJ -> VM -> CGL -> TBM -> MAS

new_segments = [
    # 12642: KKDI -> SVG -> MDU
    ('12642', 1, 'KKDI', '', '08:30', 0.0),
    ('12642', 2, 'SVG', '09:33', '09:35', 52.0),
    ('12642', 3, 'MDU', '10:40', '', 104.0),

    # 22636: MAS -> CGL -> VM -> TPJ -> MDU -> SVG -> KKDI
    ('22636', 1, 'MAS', '', '09:00', 0.0),
    ('22636', 2, 'CGL', '10:05', '10:07', 71.0),
    ('22636', 3, 'VM', '11:50', '11:55', 181.0),
    ('22636', 4, 'TPJ', '14:40', '14:45', 321.0),
    ('22636', 5, 'MDU', '16:10', '16:15', 387.0),
    ('22636', 6, 'SVG', '17:20', '17:22', 439.0),
    ('22636', 7, 'KKDI', '18:25', '', 491.0),

    # 22637: KKDI -> SVG -> MDU -> TPJ -> VM -> CGL -> MAS
    ('22637', 1, 'KKDI', '', '07:00', 0.0),
    ('22637', 2, 'SVG', '08:05', '08:07', 52.0),
    ('22637', 3, 'MDU', '09:10', '09:15', 104.0),
    ('22637', 4, 'TPJ', '10:45', '10:50', 170.0),
    ('22637', 5, 'VM', '13:35', '13:40', 310.0),
    ('22637', 6, 'CGL', '15:20', '15:22', 420.0),
    ('22637', 7, 'MAS', '16:30', '', 491.0),

    # 12639: TN -> MDU
    ('12639', 1, 'TN', '', '12:30', 0.0),
    ('12639', 2, 'MDU', '15:00', '', 160.0),

    # 16732: MAS -> TBM -> CGL -> VM -> TPJ -> MDU -> TN
    ('16732', 1, 'MAS', '', '20:00', 0.0),
    ('16732', 2, 'TBM', '20:45', '20:47', 32.0),
    ('16732', 3, 'CGL', '21:20', '21:22', 71.0),
    ('16732', 4, 'VM', '23:00', '23:05', 181.0),
    ('16732', 5, 'TPJ', '02:30', '02:35', 321.0),
    ('16732', 6, 'MDU', '04:00', '04:05', 387.0),
    ('16732', 7, 'TN', '06:30', '', 547.0),

    # 16733: TN -> MDU -> TPJ -> VM -> CGL -> TBM -> MAS
    ('16733', 1, 'TN', '', '19:00', 0.0),
    ('16733', 2, 'MDU', '21:30', '21:35', 160.0),
    ('16733', 3, 'TPJ', '23:05', '23:10', 226.0),
    ('16733', 4, 'VM', '02:35', '02:40', 366.0),
    ('16733', 5, 'CGL', '04:15', '04:17', 476.0),
    ('16733', 6, 'TBM', '04:50', '04:52', 515.0),
    ('16733', 7, 'MAS', '05:35', '', 547.0),

    # 16382: MAS -> TBM -> CGL -> VM -> TPJ -> MDU -> TEN -> NCJ -> CAPE (different route: avoids DG, goes direct MDU->TEN)
    ('16382', 1, 'MAS', '', '16:30', 0.0),
    ('16382', 2, 'TBM', '17:15', '17:17', 32.0),
    ('16382', 3, 'CGL', '17:50', '17:52', 71.0),
    ('16382', 4, 'VM', '19:30', '19:35', 181.0),
    ('16382', 5, 'TPJ', '22:05', '22:10', 321.0),
    ('16382', 6, 'MDU', '23:40', '23:45', 387.0),
    ('16382', 7, 'TEN', '02:30', '02:35', 502.0),
    ('16382', 8, 'NCJ', '03:55', '04:00', 560.0),
    ('16382', 9, 'CAPE', '04:30', '', 591.0),

    # 16381: CAPE -> NCJ -> TEN -> MDU -> TPJ -> VM -> CGL -> TBM -> MAS
    ('16381', 1, 'CAPE', '', '20:00', 0.0),
    ('16381', 2, 'NCJ', '20:30', '20:35', 31.0),
    ('16381', 3, 'TEN', '21:55', '22:00', 89.0),
    ('16381', 4, 'MDU', '00:45', '00:50', 204.0),
    ('16381', 5, 'TPJ', '02:20', '02:25', 270.0),
    ('16381', 6, 'VM', '05:10', '05:15', 410.0),
    ('16381', 7, 'CGL', '06:50', '06:52', 520.0),
    ('16381', 8, 'TBM', '07:25', '07:27', 559.0),
    ('16381', 9, 'MAS', '08:10', '', 591.0),
]

# Append to trains.csv
with open('data/trains.csv', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove trailing newline if any, then append
content = content.rstrip('\r\n')
new_lines = []
for t in new_trains:
    line = f'{t["train_number"]},{t["train_name"]},{t["train_type"]},{t["source_station"]},{t["destination_station"]},"{t["days_of_operation"]}"'
    new_lines.append(line)

with open('data/trains.csv', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content + '\r\n')
    f.write('\r\n'.join(new_lines) + '\r\n')

print('Trains appended:', len(new_trains))

# Append to segments.csv
with open('data/segments.csv', 'r', encoding='utf-8') as f:
    seg_content = f.read()

seg_content = seg_content.rstrip('\r\n')
seg_lines = []
for s in new_segments:
    train_num, seq, code, arr, dep, dist = s
    line = f'{train_num},{seq},{code},{arr},{dep},{dist}'
    seg_lines.append(line)

with open('data/segments.csv', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(seg_content + '\r\n')
    f.write('\r\n'.join(seg_lines) + '\r\n')

print('Segments appended:', len(new_segments))
print('Done.')
