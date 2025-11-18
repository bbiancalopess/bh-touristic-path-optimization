from dataclasses import dataclass


@dataclass
class Place:
    id: int
    name: str
    address: str
    lat: float
    lng: float
    opening_time: str
    closing_time: str