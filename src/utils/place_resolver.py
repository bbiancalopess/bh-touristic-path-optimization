from typing import Dict, List, Optional
import os
import csv
import math

from src.datasources.models import Place
from src.utils.fuzzy_search import search_on_csv
from src.datasources.maps_api import search_place_on_google
from src.ui.user_interface import confirm_location, display_info, display_success


def resolve_place(typed_name: str, places: List[Place], api_key: str) -> Optional[Place]:
    """
    Resolve a place name to a location from the database or Google Maps.
    
    Process:
    1. Try fuzzy matching against existing spots in CSV
    2. If not found or not confirmed, search on Google Maps
    3. Check for duplicates before saving new locations
    
    Args:
        typed_name: User-typed name of the location
        places: List of existing spots from database
        api_key: Google Maps API key
    
    Returns:
        Place or None if not found
    """

    place, score = search_on_csv(typed_name, places)

    if place is not None:
        if confirm_location(
            place.name,
            place.address or "",
            'CSV',
            confidence=score
        ):
            return place
        else:
            print("Buscando outras opções...")

    display_info(f"Não encontrado no CSV (score {score:.1f}%). Buscando no Google Maps...")
    
    google_place = search_place_on_google(typed_name, api_key)

    if google_place is None:
        print("❌ Google Maps não encontrou esse local.")
        return None
    
    if not confirm_location(
        google_place['name'],
        google_place['address'],
        'Google Maps'
    ):
        print("❌ Busca cancelada.")
        return None

    # Check for duplicates by coordinates
    duplicate = find_duplicate_by_coordinates(
        google_place['lat'],
        google_place['lng'],
        places
    )
    
    if duplicate:
        display_info(f"Este local já existe no banco de dados como: {duplicate.name}")
        use_existing = input("Deseja usar o local existente? (s/n): ").lower().strip()
        if use_existing == 's':
            return duplicate
        else:
            print("❌ Operação cancelada.")
            return None
    
    new_place = save_new_place_to_csv(google_place)
    return Place(**new_place)


def find_duplicate_by_coordinates(
    lat: float,
    lng: float,
    places: List[Place],
    threshold_meters: float = 50
) -> Optional[Place]:
    """
    Check if a location already exists based on coordinates.
    threshold_meters: maximum distance in meters to consider as duplicate
    """
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points on Earth using Haversine formula."""
        # Earth radius in meters
        earth_radius_meters = 6371000
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = earth_radius_meters * c
        
        return distance
    
    for place in places:
        dist = haversine_distance(lat, lng, place.lat, place.lng)
        if dist <= threshold_meters:
            return place
    
    return None


def save_new_place_to_csv(
    new_place: Dict,
    csv_path: str = "src/datasources/touristic_spots.csv"
) -> Dict:
    """
    Add a new place to the CSV file with automatic ID generation.
    
    Args:
        new_place: Dictionary with 'name', 'address', 'lat', 'lng' keys
        existing_spots: List of existing spots (unused but kept for compatibility)
        csv_path: Path to the CSV file
    
    Returns:
        Dictionary with the saved place data including generated ID
    """

    # Read existing data
    existing_rows = []
    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
    
    # Generate new ID
    if len(existing_rows) == 0:
        new_id = 0
    else:
        new_id = max(int(row["id"]) for row in existing_rows) + 1
    
    # Create complete row
    new_row = {
        "id": new_id,
        "name": new_place["name"],
        "address": new_place["address"],
        "lat": new_place["lat"],
        "lng": new_place["lng"],
        "opening_time": "00:00",
        "closing_time": "23:59"
    }
    
    # Save to CSV
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "name", "address", "lat", "lng", "opening_time", "closing_time"]
        )

        # Write header if CSV is empty
        if f.tell() == 0:
            writer.writeheader()
        
        writer.writerow(new_row)
    
    display_success(f"Novo lugar salvo no CSV com id={new_id}: {new_place['name']}")
    
    return new_row