from typing import List, Tuple
from models import LandZ, Plan, DispatchChoice, Building, Hero
from selector import evaluate_mission_with_available


def _consume_pool(available_heroes: List[Hero], chosen_for_building: List[Hero]) -> List[Hero]:
    """Return a new pool with heroes used for a building removed."""
    used_ids = {h.tokenId for h in chosen_for_building}
    return [h for h in available_heroes if h.tokenId not in used_ids]


def _is_building_in_progress(building: Building) -> bool:
    """Consider a building busy if it has a pending reward or a non-empty herozList."""
    return bool(building.pendingReward or building.herozList)


def build_plan(api, lands: List[LandZ], hero_pool: List[Hero]) -> Plan:
    """Create an ordered plan of dispatch choices across all lands/buildings."""
    dispatchable: List[Tuple[int, DispatchChoice]] = []
    reservations: List[DispatchChoice] = []
    candidates: List[Tuple[LandZ, Building]] = []

    # Collect all candidate buildings that are not busy
    for land in lands:
        for building in land.buildings:
            if _is_building_in_progress(building):
                print(f"[FILTER] Skip in-progress: land={land.tokenId} name={building.name}")
                continue
            candidates.append((land, building))

    # Sort by building grade (desc) then by name for stability
    candidates.sort(key=lambda lb: (lb[1].grade, lb[1].name), reverse=True)

    working_pool = hero_pool[:]
    for land, building in candidates:
        choice = evaluate_mission_with_available(working_pool, building, land.tokenId, land.name)
        if choice.chosen_heroes:
            dispatchable.append((building.grade, choice))
            working_pool = _consume_pool(working_pool, choice.chosen_heroes)
        else:
            reservations.append(choice)

    # Order dispatchable choices by (grade desc, estimated_total_points desc)
    dispatchable.sort(key=lambda item: (item[0], item[1].estimated_total_points), reverse=True)
    ordered = [choice for _, choice in dispatchable]

    # Order reservations by (grade desc, base_points desc)
    reservations.sort(key=lambda c: (c.grade, c.base_points), reverse=True)

    return Plan(choices=ordered + reservations)