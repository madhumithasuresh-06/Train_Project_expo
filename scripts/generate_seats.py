#!/usr/bin/env python3
import csv
import random
from pathlib import Path

random.seed(42)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CLASSES = ["SL", "3A", "2A", "1A", "CC", "2S"]

def get_classes_for_train(ttype):
    if ttype in ["superfast", "express"]:
        return ["SL", "3A", "2A", "1A", "2S"]
    elif ttype in ["passenger", "local", "suburban"]:
        return ["2S", "CC"]
    else:
        return ["2S"]

def main():
    trains_file = DATA_DIR / "trains.csv"
    if not trains_file.exists():
        print("trains.csv not found, please generate dataset first.")
        return

    trains = []
    with open(trains_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trains.append(row)

    seats_rows = []
    
    for train in trains:
        tnum = train["train_number"]
        ttype = train["train_type"]
        days = train["days_of_operation"].split(",")
        
        train_classes = get_classes_for_train(ttype)
        
        for day in days:
            for cls in train_classes:
                # Randomize seat availability. Some might be 0 to show waitlist.
                if random.random() < 0.15: # 15% chance of 0 seats
                    available = 0
                else:
                    available = random.randint(1, 200)
                    
                seats_rows.append({
                    "train_number": tnum,
                    "day_of_week": day,
                    "class": cls,
                    "available_seats": available
                })

    seats_file = DATA_DIR / "seat_availability.csv"
    with open(seats_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["train_number", "day_of_week", "class", "available_seats"])
        writer.writeheader()
        writer.writerows(seats_rows)
        
    print(f"Generated seat_availability.csv with {len(seats_rows)} records.")

if __name__ == "__main__":
    main()
