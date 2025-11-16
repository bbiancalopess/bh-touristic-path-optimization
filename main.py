from src.datasources.maps_api import get_google_matrix
from src.modelagem import criar_modelo
from src.datasources.load_places import load_spots

from src.routes.google_link import generate_google_link
from src.utils.time_utils import h2m
from src.utils.place_resolver import place_resolver
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def choose_from_list(spots, message="Escolha um local:"):
    """Let user choose from a list of spots or enter custom name"""
    print(f"\n{message}")
    for i, s in enumerate(spots):
        print(f"{i+1:2d}. {s['name']}")
    print(f"{len(spots)+1:2d}. Outro local (digitar nome)")
    
    while True:
        try:
            choice = int(input("\nEscolha uma opção: "))
            if 1 <= choice <= len(spots):
                return spots[choice-1], None
            elif choice == len(spots) + 1:
                custom_name = input("Digite o nome do local: ")
                return None, custom_name
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError:
            print("Por favor, digite um número.")

def choose_spots(spots):
    print("\n=== Lista de Pontos Turísticos ===")
    for s in spots:
        print(f"{s["id"]}: {s["name"]}")

    print("\nDigite os IDs dos lugares que deseja visitar (separados por vírgula):")
    ids = input(" → ").replace(" ", "").split(",")
    ids = list(map(int, ids))

    # Get stay time for each place
    stay_times = {}
    print("\nDigite o tempo de permanência (em minutos) para cada local:")
    for id in ids:
        place_name = next(s['name'] for s in spots if s['id'] == id)
        while True:
            try:
                time = int(input(f" {place_name}: "))
                if time > 0:
                    stay_times[id] = time
                    break
                else:
                    print("Por favor, digite um número positivo.")
            except ValueError:
                print("Por favor, digite um número válido.")
    
    return ids, stay_times

def main():
    spots = load_spots()

    # Choose origin
    origin_spot, origin_name = choose_from_list(spots, "Escolha o local de ORIGEM:")
    if origin_spot:
        origin = origin_spot
    else:
        origin = place_resolver(origin_name, spots, API_KEY)
        if origin:
            spots = load_spots()  # Reload to get the new spot
    
    # Choose destination
    destination_spot, destination_name = choose_from_list(spots, "Escolha o local de DESTINO:")
    if destination_spot:
        destination = destination_spot
    else:
        destination = place_resolver(destination_name, spots, API_KEY)
        if destination:
            spots = load_spots()  # Reload to get the new spot
    
    # Validate origin and destination
    if not origin or not destination:
        print("\nErro: Não foi possível encontrar origem ou destino.")
        return

    visit_ids, stay_times = choose_spots(spots)
    
    # Build the visited list properly handling circular routes
    if origin["id"] == destination["id"]:
        # For circular routes, ensure we don't duplicate the origin in the middle
        visited_set = set(visit_ids)
        visited_set.discard(origin["id"])  # Remove origin if it was selected as intermediate
        visited = [origin["id"]] + list(visited_set) + [destination["id"]]
    else:
        visited = sorted(set([origin["id"]] + visit_ids + [destination["id"]]))

    # Create places list maintaining order of visited
    places = []
    for vid in visited:
        place = next(l for l in spots if l["id"] == vid)
        places.append(place)

    c = get_google_matrix(places, API_KEY)

    # Stay times and time windows
    s = {}
    a = {}
    b = {}
    for k, place_id in enumerate(visited):
        place = next(p for p in places if p['id'] == place_id)
        # Use user-defined stay time or default to 0 for origin/destination
        if place_id in stay_times:
            s[k] = stay_times[place_id]
        elif place_id == origin['id'] or place_id == destination['id']:
            s[k] = 0
        else:
            s[k] = 60  # default 60 minutes
        
        a[k] = h2m(place['opening_time'])
        b[k] = h2m(place['closing_time'])

    nodes = list(range(len(places)))
    origin = nodes[0]
    dest = nodes[-1]

    # Create optimization model
    model, x, u, T = criar_modelo(nodes, origin, dest, c, s, a, b)

    # Disable Gurobi output
    model.setParam('OutputFlag', 0)
    
    print("\nOtimizando...")
    model.optimize()

    if model.Status == 2:
        succ = {}
        for (i, j), var in x.items():
            if var.X > 0.5:
                succ[i] = j

        rota = [origin]
        atual = origin
        while atual != dest:
            atual = succ[atual]
            rota.append(atual)

        print("\nRota ótima:")
        for i, node in enumerate(rota):
            place = places[node]
            print(f"{i+1}. {place['name']}")

        # Generate Google Maps link
        link = generate_google_link(places, rota)
        print("\nRota Google Maps:\n", link)

    else:
        print("Nenhuma solução encontrada.")


if __name__ == "__main__":
    main()