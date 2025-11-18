from typing import List, Tuple, Optional

from rapidfuzz import fuzz, process

from src.datasources.models import Place


def search_on_csv(typed_name, places: List[Place], threshold=80) -> Tuple[Optional[Place], int]:
    """
    Searches a spot by name using fuzzy matching.
    threshold defines the minimum similarity percentage.
    """
    names = [p.name for p in places]

    best, score, idx = process.extractOne(
        typed_name, names, scorer=fuzz.WRatio
    )

    if score > threshold:
        return places[idx], score

    return None, score