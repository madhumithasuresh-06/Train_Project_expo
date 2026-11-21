import pandas as pd
import random

stations = pd.read_csv("data/stations.csv")
new_stations = pd.DataFrame([
    {"station_code": "CAPE", "station_name": "Kanniyakumari", "zone": "SR", "division": "TVC", "latitude": 8.0883, "longitude": 77.5385, "is_junction": False},
    {"station_code": "NCJ", "station_name": "Nagercoil Jn", "zone": "SR", "division": "TVC", "latitude": 8.1883, "longitude": 77.4277, "is_junction": True},
    {"station_code": "TN", "station_name": "Tuticorin", "zone": "SR", "division": "MDU", "latitude": 8.7997, "longitude": 78.1360, "is_junction": False},
])
stations = pd.concat([stations, new_stations], ignore_index=True)
stations.to_csv("data/stations.csv", index=False)

trains = pd.read_csv("data/trains.csv")
new_trains = pd.DataFrame([
    {"train_number": 12633, "train_name": "Kanyakumari Express", "train_type": "superfast", "source_station": "MAS", "destination_station": "CAPE", "days_of_operation": "Mon,Tue,Wed,Thu,Fri,Sat,Sun"}
])
trains = pd.concat([trains, new_trains], ignore_index=True)
trains.to_csv("data/trains.csv", index=False)

segments = pd.read_csv("data/segments.csv")
new_segments = pd.DataFrame([
    {"train_number": 12633, "stop_sequence": 1, "station_code": "MAS", "scheduled_arrival": None, "scheduled_departure": "17:20", "distance_from_source_km": 0},
    {"train_number": 12633, "stop_sequence": 2, "station_code": "MS", "scheduled_arrival": "17:35", "scheduled_departure": "17:40", "distance_from_source_km": 8},
    {"train_number": 12633, "stop_sequence": 3, "station_code": "TBM", "scheduled_arrival": "18:05", "scheduled_departure": "18:10", "distance_from_source_km": 33},
    {"train_number": 12633, "stop_sequence": 4, "station_code": "CGL", "scheduled_arrival": "18:40", "scheduled_departure": "18:42", "distance_from_source_km": 64},
    {"train_number": 12633, "stop_sequence": 5, "station_code": "VM", "scheduled_arrival": "20:05", "scheduled_departure": "20:10", "distance_from_source_km": 167},
    {"train_number": 12633, "stop_sequence": 6, "station_code": "TPJ", "scheduled_arrival": "22:40", "scheduled_departure": "22:45", "distance_from_source_km": 345},
    {"train_number": 12633, "stop_sequence": 7, "station_code": "MDU", "scheduled_arrival": "01:25", "scheduled_departure": "01:30", "distance_from_source_km": 501},
    {"train_number": 12633, "stop_sequence": 8, "station_code": "TEN", "scheduled_arrival": "04:15", "scheduled_departure": "04:20", "distance_from_source_km": 658},
    {"train_number": 12633, "stop_sequence": 9, "station_code": "NCJ", "scheduled_arrival": "05:40", "scheduled_departure": "05:45", "distance_from_source_km": 732},
    {"train_number": 12633, "stop_sequence": 10, "station_code": "CAPE", "scheduled_arrival": "06:15", "scheduled_departure": None, "distance_from_source_km": 748},
])
segments = pd.concat([segments, new_segments], ignore_index=True)
segments.to_csv("data/segments.csv", index=False)

# Add dummy delay and seat availability
seats = pd.read_csv("data/seat_availability.csv")
new_seats = []
for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
    for cls in ["SL", "3A", "2A", "1A", "CC", "2S"]:
        new_seats.append({"train_number": 12633, "day_of_week": day, "class": cls, "available_seats": random.randint(10, 150)})
seats = pd.concat([seats, pd.DataFrame(new_seats)], ignore_index=True)
seats.to_csv("data/seat_availability.csv", index=False)

delays = pd.read_csv("data/delay_profile.csv")
new_delays = []
for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
    new_delays.append({"train_number": 12633, "day_of_week": day, "avg_delay_minutes": random.randint(5, 45)})
delays = pd.concat([delays, pd.DataFrame(new_delays)], ignore_index=True)
delays.to_csv("data/delay_profile.csv", index=False)

print("Done appending Kanyakumari train data!")
