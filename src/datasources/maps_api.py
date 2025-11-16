import requests


def get_google_matrix(places, api_key):
    coords = [f"{p["lat"]},{p["lng"]}" for p in places]
    coords_str = "|".join(coords)

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={coords_str}&destinations={coords_str}&key={api_key}"
    )

    r = requests.get(url).json()

    n = len(places)
    c = [[0]*n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            c[i][j] = r["rows"][i]["elements"][j]["duration"]["value"] // 60

    return c


def searches_local_places(name, api_key):
    url = (
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        f"?input={name}"
        f"&inputtype=textquery"
        f"&fields=formatted_address,name,geometry"
        f"&key={api_key}"
    )

    r = requests.get(url).json()

    if r.get("candidates") is None or len(r["candidates"]) == 0:
        return None

    place = r["candidates"][0]

    return {
        "name": place.get("name"),
        "address": place.get("formatted_address"),
        "lat": place["geometry"]["location"]["lat"],
        "lng": place["geometry"]["location"]["lng"],
    }
