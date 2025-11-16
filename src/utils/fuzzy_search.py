from rapidfuzz import fuzz, process


def search_on_csv(typed_name, spots, threshold=80):
    """
    Searches a spot by name using fuzzy matching.
    threshold defines the minimum similarity percentage.
    """
    names = [s["name"] for s in spots]

    best, score, idx = process.extractOne(
        typed_name, names, scorer=fuzz.WRatio
    )

    if score > threshold:
        return spots[idx], score

    return None, score