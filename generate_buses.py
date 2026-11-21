import csv
import random

# Major TN cities/stations: MAS (Chennai), MDU (Madurai), CBE (Coimbatore), TPJ (Trichy), TEN (Tirunelveli), SA (Salem)
routes = [
    ("MAS", "MDU", 460), ("MDU", "MAS", 460),
    ("MAS", "CBE", 510), ("CBE", "MAS", 510),
    ("MAS", "TPJ", 330), ("TPJ", "MAS", 330),
    ("MDU", "TEN", 160), ("TEN", "MDU", 160),
    ("CBE", "SA", 160), ("SA", "CBE", 160),
    ("TPJ", "MDU", 130), ("MDU", "TPJ", 130),
    ("MAS", "SA", 340), ("SA", "MAS", 340),
]

bus_types = ["SETC Ultra Deluxe", "TNSTC Non-AC", "Private AC Sleeper", "Private AC Seater"]

def mins_to_time(mins):
    h = (mins // 60) % 24
    m = mins % 60
    return f"{h:02d}:{m:02d}"

with open("data/bus_routes.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["bus_id", "source", "destination", "departure", "arrival", "bus_type", "available_seats", "price_inr"])
    
    bus_id = 1000
    for src, dst, dist in routes:
        # Generate 4-6 buses per route
        num_buses = random.randint(4, 6)
        for _ in range(num_buses):
            dep_mins = random.randint(0, 23*60)
            # average bus speed ~50km/h
            duration_mins = int((dist / 50.0) * 60) + random.randint(-30, 30)
            arr_mins = dep_mins + duration_mins
            
            b_type = random.choice(bus_types)
            seats = random.randint(0, 40)
            
            # Price ~1.5 to 3 INR per km depending on type
            multiplier = 3 if "AC Sleeper" in b_type else 2 if "Ultra Deluxe" in b_type else 1.5
            price = int(dist * multiplier)
            
            writer.writerow([
                f"BUS{bus_id}", src, dst,
                mins_to_time(dep_mins), mins_to_time(arr_mins),
                b_type, seats, price
            ])
            bus_id += 1
