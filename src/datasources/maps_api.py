"""Google Maps API integration for distance matrix and place search."""

from typing import Dict, List, Optional
import requests


def get_google_matrix(places: List[Dict], api_key: str) -> List[List[int]]:
    """
    Get travel time matrix between all places using Google Distance Matrix API.
    
    Args:
        places: List of places with 'lat' and 'lng' keys
        api_key: Google Maps API key
    
    Returns:
        2D matrix where matrix[i][j] is travel time from place i to j in minutes
    """
    # Build coordinates string
    coordinates = [f"{place['lat']},{place['lng']}" for place in places]
    coords_string = "|".join(coordinates)

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={coords_string}&destinations={coords_string}&key={api_key}"
    )

    response = requests.get(url).json()
    
    # Check for API errors
    if response.get("status") != "OK":
        raise Exception(f"Google Maps API error: {response.get('error_message', 'Unknown error')}")
    
    num_places = len(places)
    travel_times = [[0] * num_places for _ in range(num_places)]
    
    # Extract travel times in minutes
    for i in range(num_places):
        for j in range(num_places):
            element = response["rows"][i]["elements"][j]
            if element["status"] == "OK":
                travel_times[i][j] = element["duration"]["value"] // 60
            else:
                # Use a large value for unreachable destinations
                travel_times[i][j] = 999999
    
    return travel_times


def search_place_on_google(name: str, api_key: str) -> Optional[Dict]:
    """
    Search for a place using Google Places API.
    
    Args:
        name: Place name to search for
        api_key: Google Maps API key
    
    Returns:
        Dictionary with place information or None if not found
    """
    url = (
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        f"?input={name}"
        f"&inputtype=textquery"
        f"&fields=formatted_address,name,geometry"
        f"&key={api_key}"
    )

    response = requests.get(url).json()
    
    # Check if any candidates were found
    if not response.get("candidates"):
        return None
    
    # Return the first candidate
    place = response["candidates"][0]
    
    return {
        "name": place.get("name", "Unknown"),
        "address": place.get("formatted_address", ""),
        "lat": place["geometry"]["location"]["lat"],
        "lng": place["geometry"]["location"]["lng"],
    }
