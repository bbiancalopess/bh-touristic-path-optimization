"""Google Maps route link generation."""

from typing import List, Dict


def generate_google_link(places: List[Dict], route_indices: List[int]) -> str:
    """
    Generate a Google Maps URL for the optimal route.
    
    Args:
        places: List of places in optimization order
        route_indices: List of indices representing the route order
    
    Returns:
        Google Maps URL string with the route
    """
    # Build waypoints from route indices
    waypoints = []
    for index in route_indices:
        place = places[index]
        waypoints.append(f"{place['lat']},{place['lng']}")
    
    # Construct Google Maps directions URL
    base_url = "https://www.google.com/maps/dir/"
    url = base_url + "/".join(waypoints)
    
    return url