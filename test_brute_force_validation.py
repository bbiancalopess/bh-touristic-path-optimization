"""
Teste de validação por força bruta para instâncias pequenas.
Compara a solução ótima do modelo com todas as permutações possíveis.
"""

import itertools
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import time as time_module
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.datasources.load_places import load_places
from src.datasources.maps_api import get_google_matrix
from src.optimization.optimization_model import create_optimization_model
from src.utils.time_utils import hhmm_to_minutes, minutes_to_hhmm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def calculate_route_time(route: List[int], travel_times: List[List[int]], 
                        stay_times: Dict[int, int], opening_times: Dict[int, int], 
                        closing_times: Dict[int, int], start_time: int) -> Tuple[float, bool, List[int]]:
    """
    Calculate total time for a route and check if it's valid.
    
    Returns:
        Tuple of (total_travel_time, is_valid, arrival_times)
    """
    total_travel_time = 0
    current_time = start_time
    arrival_times = []
    
    for i in range(len(route)):
        # Check if we arrive within opening hours
        if current_time < opening_times[route[i]]:
            current_time = opening_times[route[i]]  # Wait for opening
        
        arrival_times.append(current_time)
        
        # Check if we can complete the visit before closing
        if current_time + stay_times[route[i]] > closing_times[route[i]]:
            return float('inf'), False, arrival_times
        
        # Add stay time
        current_time += stay_times[route[i]]
        
        # Add travel time to next location
        if i < len(route) - 1:
            travel_time = travel_times[route[i]][route[i + 1]]
            total_travel_time += travel_time
            current_time += travel_time
    
    return total_travel_time, True, arrival_times


def brute_force_solution(nodes: List[int], origin_idx: int, dest_idx: int,
                        travel_times: List[List[int]], stay_times: Dict[int, int],
                        opening_times: Dict[int, int], closing_times: Dict[int, int],
                        start_time: int) -> Tuple[List[int], float, List[Tuple[List[int], float, bool]]]:
    """
    Find optimal solution by trying all possible permutations.
    
    Returns:
        Tuple of (best_route, best_time, all_routes_info)
    """
    # Get intermediate nodes (excluding origin and destination)
    intermediate_nodes = [n for n in nodes if n != origin_idx and n != dest_idx]
    
    best_route = None
    best_time = float('inf')
    all_routes_info = []
    
    # Try all permutations of intermediate nodes
    for perm in itertools.permutations(intermediate_nodes):
        route = [origin_idx] + list(perm) + [dest_idx]
        travel_time, is_valid, arrival_times = calculate_route_time(
            route, travel_times, stay_times, opening_times, closing_times, start_time
        )
        
        all_routes_info.append((route, travel_time, is_valid))
        
        if is_valid and travel_time < best_time:
            best_time = travel_time
            best_route = route
    
    return best_route, best_time, all_routes_info


def solve_with_gurobi(nodes: List[int], origin_idx: int, dest_idx: int,
                      travel_times: List[List[int]], stay_times: Dict[int, int],
                      opening_times: Dict[int, int], closing_times: Dict[int, int],
                      start_time: int) -> Tuple[List[int], float, float]:
    """
    Solve using Gurobi optimization model.
    
    Returns:
        Tuple of (route, travel_time, solve_time)
    """
    start = time_module.time()
    
    model, x_vars, u_vars, T_vars = create_optimization_model(
        nodes, origin_idx, dest_idx, travel_times, stay_times, 
        opening_times, closing_times, start_time=start_time
    )
    
    model.setParam('OutputFlag', 0)
    model.optimize()
    
    solve_time = time_module.time() - start
    
    if model.Status == 2:
        # Extract route
        successor = {}
        for (i, j), var in x_vars.items():
            if var.X > 0.5:
                successor[i] = j
        
        route = [origin_idx]
        current = origin_idx
        while current != dest_idx:
            current = successor[current]
            route.append(current)
        
        travel_time = model.objVal
        return route, travel_time, solve_time
    else:
        return None, float('inf'), solve_time


def main():
    """Run validation test comparing Gurobi with brute force."""
    
    print("=== TESTE DE VALIDAÇÃO: GUROBI vs FORÇA BRUTA ===\n")
    
    # Load places and select a small subset for testing
    all_places = load_places()
    
    # Select specific places for test (small instance)
    test_place_ids = [1, 2, 4, 5, 8]  # 5 places total
    test_places = [p for p in all_places if p.id in test_place_ids]
    
    print(f"Testando com {len(test_places)} locais:")
    for i, place in enumerate(test_places):
        print(f"  {i}: {place.name}")
    
    # Define test parameters
    origin_idx = 0  # Praça da Liberdade
    dest_idx = 4    # Parque Municipal
    start_time = hhmm_to_minutes("09:00")
    
    print(f"\nOrigem: {test_places[origin_idx].name}")
    print(f"Destino: {test_places[dest_idx].name}")
    print(f"Horário de início: {minutes_to_hhmm(start_time)}")
    
    # Get travel times matrix
    print("\nObtendo matriz de tempos de viagem...")
    travel_times = get_google_matrix(test_places, API_KEY)
    
    # Prepare data
    nodes = list(range(len(test_places)))
    stay_times = {i: 30 if i not in [origin_idx, dest_idx] else 0 for i in nodes}
    opening_times = {i: hhmm_to_minutes(p.opening_time) for i, p in enumerate(test_places)}
    closing_times = {i: hhmm_to_minutes(p.closing_time) for i, p in enumerate(test_places)}
    
    # Run brute force
    print("\nExecutando força bruta...")
    bf_route, bf_time, all_routes = brute_force_solution(
        nodes, origin_idx, dest_idx, travel_times, stay_times,
        opening_times, closing_times, start_time
    )
    
    print(f"  Rotas avaliadas: {len(all_routes)}")
    print(f"  Melhor tempo encontrado: {bf_time:.0f} minutos")
    print(f"  Melhor rota encontrada: {bf_route}")
    
    # Run Gurobi
    print("\nExecutando Gurobi...")
    gb_route, gb_time, gb_solve_time = solve_with_gurobi(
        nodes, origin_idx, dest_idx, travel_times, stay_times,
        opening_times, closing_times, start_time
    )

    print(f"  Tempo ótimo: {gb_time:.0f} minutos")
    print(f"  Melhor rota encontrada: {gb_route}")
    
    # Validation
    print("\n=== RESULTADO DA VALIDAÇÃO ===")
    if abs(gb_time - bf_time) < 0.1:
        print("✅ SUCESSO: Gurobi encontrou a mesma solução ótima da força bruta!")
    else:
        print("❌ ERRO: As soluções divergem!")
        print(f"   Diferença: {abs(gb_time - bf_time):.1f} minutos")

    # Show all valid routes sorted by time
    print("\n=== TODAS AS ROTAS VÁLIDAS (ordenadas por tempo) ===")
    valid_routes = [(r, t) for r, t, v in all_routes if v]
    valid_routes.sort(key=lambda x: x[1])
    
    for i, (route, time) in enumerate(valid_routes[:10]):  # Show top 10
        route_str = ' → '.join([test_places[idx].name.split(',')[0] for idx in route])
        is_optimal = "⭐" if route == gb_route else "  "
        print(f"{is_optimal} {i+1:2d}. {time:3.0f} min: {route_str}")
    
    if len(valid_routes) > 10:
        print(f"... e mais {len(valid_routes) - 10} rotas")
    
    plt.show()


if __name__ == "__main__":
    main()