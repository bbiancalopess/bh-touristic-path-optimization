import csv
from typing import List

from src.datasources.models import Place


def load_places(path: str ="src/datasources/touristic_spots.csv") -> List[Place]:
    places = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            places.append(Place(
                id=int(row["id"]),
                name=row["name"],
                address=row["address"],
                lat=float(row["lat"]),
                lng=float(row["lng"]),
                opening_time=row["opening_time"],
                closing_time=row["closing_time"],
            ))

    return places