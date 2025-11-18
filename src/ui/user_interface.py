"""User interface functions for the touristic path optimization application."""

from typing import List, Dict, Tuple, Optional

from src.datasources.models import Place


def choose_from_list(places: List[Place], message: str = "Escolha um local:") -> Tuple[Optional[Place], Optional[str]]:
    """
    Let user choose from a list of places or enter a custom name.
    
    Args:
        places: List of available spots
        message: Message to display to user
    
    Returns:
        Tuple of (selected_spot, custom_name)
        If spot is selected from list, returns (spot, None)
        If custom name is entered, returns (None, custom_name)
    """
    print(f"\n{message}")
    for i, place in enumerate(places):
        print(f"{i+1:2d}. {place.name}")
    print(f"{len(places) + 1:2d}. Outro local (digitar nome)")
    
    while True:
        try:
            choice = int(input("\nEscolha uma opção: "))
            if 1 <= choice <= len(places):
                return places[choice - 1], None
            elif choice == len(places) + 1:
                custom_name = input("Digite o nome do local: ")
                return None, custom_name
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("Por favor, digite um número.")


def choose_spots_to_visit(places: List[Place]) -> Tuple[List[int], Dict[int, int]]:
    """
    Let user choose which spots to visit and their stay times.
    
    Args:
        places: List of all available spots
    
    Returns:
        Tuple of (spot_ids, stay_times_dict)
    """
    print("\n=== Lista de Pontos Turísticos ===")
    for place in places:
        print(f"{place.id:2d}: {place.name}")
    
    print("\nDigite os IDs dos lugares que deseja visitar (separados por vírgula):")
    ids_input = input(" → ").replace(" ", "").split(",")
    places_ids = list(map(int, ids_input))
    
    # Get stay time for each place
    stay_times = {}
    print("\nDigite o tempo de permanência (em minutos) para cada local:")
    for place_id in places_ids:
        place_name = next(p.name for p in places if p.id == place_id)
        while True:
            try:
                time = int(input(f" {place_name}: "))
                if time > 0:
                    stay_times[place_id] = time
                    break
                else:
                    print("Por favor, digite um número positivo.")
            except ValueError:
                print("Por favor, digite um número válido.")
    
    return places_ids, stay_times


def confirm_location(location_name: str, location_address: str, source: str, confidence: float = None) -> bool:
    """
    Ask user to confirm if the found location is correct.
    
    Args:
        location_name: Name of the location
        location_address: Address of the location
        source: Where the location was found (CSV or Google Maps)
        confidence: Confidence score for fuzzy matching (optional)
    
    Returns:
        True if user confirms, False otherwise
    """
    print(f"\n📍 Encontrado no {source}{f' (confiança {confidence:.1f}%)' if confidence else ''}:")
    print(f"   Nome: {location_name}")
    print(f"   Endereço: {location_address if location_address else 'Não disponível'}")
    
    response = input("\nEste é o local correto? (s/n): ").lower().strip()
    return response == 's'


def display_optimal_route(
    places: List[Place],
    route_indices: List[int], 
    arrival_times: Dict[int, float],
    stay_times: Dict[int, int],
    total_travel_time: int,
    total_route_duration: int = None
) -> None:
    """
    Display the optimal route to the user with timing information.
    
    Args:
        places: List of places in the order they appear in the optimization
        route_indices: List of indices representing the optimal route
        arrival_times: Dictionary mapping node index to arrival time (minutes from midnight)
        stay_times: Dictionary mapping node index to stay time in minutes
        total_travel_time: Total time spent in transit (minutes)
        total_route_duration: Total duration from start to end (minutes)
    """
    def minutes_to_time(minutes: float) -> str:
        """Convert minutes from midnight to HH:MM format."""
        total_mins = int(round(minutes))
        hours = total_mins // 60
        mins = total_mins % 60
        # Handle cases where time exceeds 24 hours
        if hours >= 24:
            days = hours // 24
            hours = hours % 24
            return f"{hours:02d}:{mins:02d} (+{days}d)"
        return f"{hours:02d}:{mins:02d}"
    
    print("\nRota ótima com horários:")
    print("-" * 60)
    
    for i, node_index in enumerate(route_indices):
        place = places[node_index]
        arrival = arrival_times[node_index]
        stay = stay_times[node_index]
        departure = arrival + stay
        
        print(f"{i+1}. {place.name}")
        print(f"   Chegada: {minutes_to_time(arrival)}")
        if stay > 0:
            print(f"   Permanência: {stay} minutos")
            print(f"   Saída: {minutes_to_time(departure)}")
        print()
    
    print("-" * 60)
    print(f"Tempo em trânsito: {total_travel_time} minutos ({total_travel_time // 60}h {total_travel_time % 60}min)")
    
    if total_route_duration is not None:
        print(f"Duração total da rota: {total_route_duration} minutos ({total_route_duration // 60}h {total_route_duration % 60}min)")


def ask_for_starting_time() -> int:
    print("\nQual horário deseja iniciar a rota? (formato HH:MM, ex: 08:30)")
    while True:
        try:
            start_time = input(" → ").strip()
            hours, minutes = map(int, start_time.split(":"))
            if 0 <= hours < 24 and 0 <= minutes < 60:
                start_minutes = hours * 60 + minutes
                return start_minutes
            else:
                print("Horário inválido. Use formato HH:MM (ex: 08:30)")
        except:
            print("Formato inválido. Use HH:MM (ex: 08:30)")


def display_error(message: str) -> None:
    """Display an error message to the user."""
    print(f"\n❌ {message}")


def display_info(message: str) -> None:
    """Display an informational message to the user."""
    print(f"\n⚠️ {message}")


def display_success(message: str) -> None:
    """Display a success message to the user."""
    print(f"\n✔ {message}")