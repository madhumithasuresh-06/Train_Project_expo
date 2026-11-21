import csv

# Check details on SVG and TN - the ones with only 1 train
for code in ['SVG', 'TN', 'KRR', 'TJ', 'KMU', 'MV', 'RMM', 'VLR']:
    with open('data/segments.csv', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r['station_code'] == code]
    with open('data/trains.csv', encoding='utf-8') as f:
        trains = [r for r in csv.DictReader(f) if r['source_station'] == code or r['destination_station'] == code]
    print(code + ': ' + str(len(rows)) + ' segment rows, ' + str(len(trains)) + ' as src/dest')
    for t in trains:
        print('  ' + t['train_number'] + ' ' + t['train_name'] + ' (' + t['source_station'] + '-->' + t['destination_station'] + ')')
    for r in rows[:3]:
        print('  seg: train ' + r['train_number'] + ' stop#' + r['stop_sequence'])
