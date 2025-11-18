"""
BH Touristic Path Optimization
Main entry point for the application.
"""

from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv

from src.datasources.models import Place
from src.datasources.load_places import load_places
from src.datasources.maps_api import get_google_matrix
from src.optimization.optimization_model import create_optimization_model
from src.routes.google_link import generate_google_link
from src.utils.time_utils import hhmm_to_minutes
from src.utils.place_resolver import resolve_place
from src.ui.user_interface import (
    choose_from_list,
    choose_spots_to_visit,
    display_optimal_route,
    display_error, ask_for_starting_time,
)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def get_origin_and_destination(places: List[Place]) -> Tuple[Place, Place, List[Place]]:
    """Get origin and destination from user input.
    
    Returns:
        Tuple of (origin, destination, updated_spots)
    """
    # Choose origin
    origin_spot, origin_name = choose_from_list(places, "Escolha o local de ORIGEM:")
    if origin_spot:
        origin = origin_spot
    else:
        origin = resolve_place(origin_name, places, API_KEY)
        if origin:
            places = load_places()  # Reload to get the new spot
    
    # Choose destination
    destination_spot, destination_name = choose_from_list(places, "Escolha o local de DESTINO:")
    if destination_spot:
        destination = destination_spot
    else:
        destination = resolve_place(destination_name, places, API_KEY)
        if destination:
            places = load_places()  # Reload to get the new spot
    
    return origin, destination, places


def build_route_places(
    origin_id: int,
    destination_id: int,
    intermediate_ids: List[int],
    all_places: List[Place]
) -> Tuple[List[int], List[Place]]:
    """
    Build the ordered list of places for the route.
    
    Returns:
        Tuple of (visited_ids, places_list)
    """
    # Build the visited list properly handling circular routes
    if origin_id == destination_id:
        # For circular routes, ensure we don't duplicate the origin in the middle
        visited_set = set(intermediate_ids)
        visited_set.discard(origin_id)  # Remove origin if selected as intermediate
        places_to_visit_ids = [origin_id] + list(visited_set) + [destination_id]
    else:
        # For open routes, keep origin first and destination last
        intermediate_set = set(intermediate_ids)
        intermediate_set.discard(origin_id)  # Remove if accidentally included
        intermediate_set.discard(destination_id)  # Remove if accidentally included
        places_to_visit_ids = [origin_id] + list(intermediate_set) + [destination_id]
    
    # Create places list maintaining order of visited
    places = []
    for place_id in places_to_visit_ids:
        place = next(p for p in all_places if p.id == place_id)
        places.append(place)
    
    return places_to_visit_ids, places


def prepare_optimization_data(
    places_to_visit_ids: List[int],
    places: List[Place],
    stay_times: Dict[int, int],
    origin_id: int,
    destination_id: int
) -> Tuple[Dict[int, int], Dict[int, int], Dict[int, int]]:
    """Prepare stay times and time windows for optimization."""
    s = {}  # Stay times
    a = {}  # Opening times
    b = {}  # Closing times
    
    for k, place_id in enumerate(places_to_visit_ids):
        place = next(p for p in places if p.id == place_id)
        
        # Use user-defined stay time or default to 0 for origin/destination
        if place_id in stay_times:
            s[k] = stay_times[place_id]
        elif place_id == origin_id or place_id == destination_id:
            s[k] = 0
        else:
            s[k] = 60  # default 60 minutes
        
        a[k] = hhmm_to_minutes(place.opening_time)
        b[k] = hhmm_to_minutes(place.closing_time)
    
    return s, a, b


def extract_optimal_route(x_vars: Dict, origin_idx: int, dest_idx: int) -> List[int]:
    """Extract the optimal route from the solution."""
    successor = {}
    for (i, j), var in x_vars.items():
        if var.X > 0.5:
            successor[i] = j
    
    route = [origin_idx]
    current = origin_idx
    while current != dest_idx:
        current = successor[current]
        route.append(current)
    
    return route


def main():
    """Main function for the touristic path optimization application."""
    # Load touristic spots
    places = load_places()
    
    # Get origin and destination
    origin, destination, places = get_origin_and_destination(places)
    
    # Validate origin and destination
    if not origin or not destination:
        display_error("Não foi possível encontrar origem ou destino.")
        return
    
    # Choose intermediate spots and get stay times
    places_ids, stay_times = choose_spots_to_visit(places)
    
    # Get start time
    start_minutes = ask_for_starting_time()

    # Build route places
    places_to_visit_ids, places = build_route_places(
        origin.id,
        destination.id,
        places_ids,
        places
    )
    
    # Get travel time matrix from Google Maps
    travel_cost_times = get_google_matrix(places, API_KEY)
    
    # Prepare optimization data
    s, a, b = prepare_optimization_data(
        places_to_visit_ids,
        places,
        stay_times,
        origin.id,
        destination.id
    )
    
    # Create and solve optimization model
    nodes = list(range(len(places)))
    origin_idx = nodes[0]
    dest_idx = nodes[-1]
    
    model, x_vars, u_vars, T_vars = create_optimization_model(
        nodes, origin_idx, dest_idx, travel_cost_times, s, a, b, start_time=start_minutes
    )
    
    # Disable Gurobi output
    model.setParam('OutputFlag', 0)
    
    print("\nOtimizando...")
    model.optimize()
    
    # Process results
    if model.Status == 2:  # Optimal solution found
        route = extract_optimal_route(x_vars, origin_idx, dest_idx)
        
        # Extract arrival times from solution
        arrival_times = {i: T_vars[i].X for i in nodes}
        
        # Calculate total travel time (only transit time - the objective value)
        total_travel_time = int(model.objVal)
        
        # Calculate total route duration (from start to end)
        route_start = arrival_times[route[0]]
        route_end = arrival_times[route[-1]] + s[route[-1]]  # arrival + stay time at last place
        total_route_duration = int(route_end - route_start)
        
        # Display results with timing information
        display_optimal_route(places, route, arrival_times, s, total_travel_time, total_route_duration)
        
        # Generate Google Maps link
        link = generate_google_link(places, route)
        print("\nRota Google Maps:\n", link)
    else:
        status_messages = {
            3: "Modelo inviável - verifique os horários de funcionamento e tempo disponível.",
            4: "Modelo inviável ou ilimitado.",
            5: "Solução ótima ilimitada.",
            6: "Limite de iterações atingido.",
            7: "Limite de nós atingido.",
            8: "Limite de tempo atingido.",
            9: "Limite de soluções atingido.",
            10: "Usuário interrompeu a otimização.",
            11: "Dificuldades numéricas encontradas.",
            12: "Modelo subótimo.",
            13: "Modelo carregado, mas não resolvido."
        }
        print(f"\nNenhuma solução encontrada.")
        print(f"Status do solver: {status_messages.get(model.Status, f'Status desconhecido ({model.Status})')}")
        
        # Sugestões
        print("\nPossíveis causas:")
        print("- Horários de funcionamento incompatíveis com o roteiro")
        print("- Tempo insuficiente para visitar todos os locais")
        print("- Horário de início muito tarde")


if __name__ == "__main__":
    main()