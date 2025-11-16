import csv


def load_spots(path="src/datasources/touristic_spots.csv"):
    spots = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            spots.append({
                "id": int(row["id"]),
                "name": row["name"],
                "address": row["address"],
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
                "opening_time": row["opening_time"],
                "closing_time": row["closing_time"],
            })

    return spots