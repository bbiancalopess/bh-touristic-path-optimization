from src.utils.fuzzy_search import search_on_csv
from src.datasources.maps_api import searches_local_places
import os
import csv
import math


def place_resolver(typed_name, spots, api_key):
    """
    Tries to solve the place:
    1. Fuzzy match on csv
    2. Search on Google Maps
    """

    place, score = search_on_csv(typed_name, spots)

    if place is not None:
        print(f"\n📍 Encontrado no CSV (confiança {score:.1f}%):")
        print(f"   Nome: {place['name']}")
        print(f"   Endereço: {place.get('address', 'Não disponível')}")
        
        confirm = input("\nEste é o local correto? (s/n): ").lower().strip()
        if confirm == 's':
            return place
        else:
            print("Buscando outras opções...")

    print(f"⚠ Não encontrado no CSV (score {score:.1f}%). Buscando no Google Maps...")

    mapa = searches_local_places(typed_name, api_key)

    if mapa is None:
        print("❌ Google Maps não encontrou esse local.")
        return None

    print(f"\n📍 Local encontrado no Google Maps:")
    print(f"   Nome: {mapa['name']}")
    print(f"   Endereço: {mapa['address']}")
    
    confirm = input("\nEste é o local correto? (s/n): ").lower().strip()
    if confirm != 's':
        print("❌ Busca cancelada.")
        return None

    # Check for duplicates by coordinates
    duplicate = check_duplicate_by_coordinates(mapa['lat'], mapa['lng'], spots)
    if duplicate:
        print(f"\n⚠️ Este local já existe no banco de dados como: {duplicate['name']}")
        use_existing = input("Deseja usar o local existente? (s/n): ").lower().strip()
        if use_existing == 's':
            return duplicate
        else:
            print("❌ Operação cancelada.")
            return None

    novo = salvar_novo_lugar_csv(mapa, spots)

    return novo


def check_duplicate_by_coordinates(lat, lng, spots, threshold_meters=50):
    """
    Check if a location already exists based on coordinates.
    threshold_meters: maximum distance in meters to consider as duplicate
    """
    def haversine_distance(lat1, lon1, lat2, lon2):
        # Earth radius in meters
        R = 6371000
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    for spot in spots:
        distance = haversine_distance(lat, lng, spot['lat'], spot['lng'])
        if distance <= threshold_meters:
            return spot
    
    return None

def salvar_novo_lugar_csv(novo_lugar, spots, path="src/datasources/touristic_spots.csv"):
    """
    Adiciona um novo lugar ao CSV com ID automático.
    novo_lugar deve conter: nome, lat, lon
    """

    # Ler dados existentes
    linhas = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                linhas.append(row)

    # Gerar novo ID
    if len(linhas) == 0:
        novo_id = 0
    else:
        novo_id = max(int(l["id"]) for l in linhas) + 1

    # Criar linha completa
    nova_linha = {
        "id": novo_id,
        "name": novo_lugar["name"],
        "address": novo_lugar["address"],
        "lat": novo_lugar["lat"],
        "lng": novo_lugar["lng"],
        "opening_time": "00:00",
        "closing_time": "23:59"
    }

    # Salvar no CSV
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "name", "address", "lat", "lng", "opening_time", "closing_time"]
        )

        # Se o CSV estiver vazio, escrever cabeçalho
        if f.tell() == 0:
            writer.writeheader()

        writer.writerow(nova_linha)

    print(f"💾 Novo lugar salvo no CSV com id={novo_id}: {novo_lugar['name']}")

    return nova_linha