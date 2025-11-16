
def generate_google_link(places, route):
    parts = []
    for i in route:
        p = places[i]
        parts.append(f"{p['lat']},{p['lng']}")

    url = "https://www.google.com/maps/dir/" + "/".join(parts)
    return url