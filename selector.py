from typing import List, Tuple
from models import Hero, Building, DispatchChoice
from config import BUILDING_HERO_COUNT, GRADE_POINTS, GRADE_BUFF_PERCENT, GRADE_MAP
from rules import hero_matches, find_all_keys, choose_fillers, pop_by_ids


def _sort_buff_easy_first(buff_mission) -> Tuple[int, int, int]:
    # Sort buffs: lower required grade first, then lower buff amount, then prefer Base > Elite > Genesis > Any
    create_type_priority = {2: 0, 1: 1, 0: 2, -1: 3}.get(buff_mission.createType, 3)
    required_grade = buff_mission.herozGrade if buff_mission.herozGrade != -1 else 0
    return (required_grade, buff_mission.buffAmount, create_type_priority)


def _match_candidates(available_heroes: List[Hero], buff_mission) -> List[Hero]:
    # Filter heroes that match buff conditions and sort by lower grade, prefer Base > Elite > Genesis, then lower stars
    return sorted(
        [hero for hero in available_heroes if hero_matches(hero, buff_mission)],
        key=lambda hero: (hero.grade, {1: 0, 2: 1, 0: 2}.get(hero.primalType, 3), hero.star, hero.tokenId)
    )


def _finalize_assignments(selected_heroes: List[Hero], building: Building) -> Tuple[int, List[str]]:
    completed_titles = []
    completed_count = 0
    for buff_mission in building.buffMissions:
        matching_heroes = [hero for hero in selected_heroes if hero_matches(hero, buff_mission)]
        if len(matching_heroes) >= buff_mission.boostConditionCount:
            completed_count += 1
            completed_titles.append(buff_mission.title + " [" + ", ".join(str(h.tokenId) for h in matching_heroes[:buff_mission.boostConditionCount]) + "]")
    return completed_count, completed_titles


def evaluate_mission_with_available(available_heroes: List[Hero], building: Building, land_token: int, land_name: str) -> DispatchChoice:
    base_points = GRADE_POINTS.get(building.grade, 0)
    buff_pct_grade = GRADE_BUFF_PERCENT.get(building.grade, 0.0)
    remaining_pool = available_heroes[:]

    # 1) Find key heroes (grade >= building grade)
    key_heroes = find_all_keys(remaining_pool, building.grade)
    if not key_heroes:
        print(f"[PLAN] No key hero found for building '{building.name}' (requires ≥ {GRADE_MAP.get(building.grade)}).")
        return DispatchChoice(
            landId=land_token,
            landName=land_name,
            buildingType=building.buildingType,
            buildingName=building.name,
            grade=building.grade,
            base_points=base_points,
            buffs_possible=0,
            buff_percent_each=buff_pct_grade,
            estimated_total_points=base_points,
            chosen_heroes=[],
            satisfied_buffs_titles=[],
            reserved_heroes=choose_fillers(remaining_pool, BUILDING_HERO_COUNT),
            reason=f"No eligible key hero (≥ {GRADE_MAP.get(building.grade)}). Reserved for future use.",
        )

    # 2) Try to satisfy buffs first (without key hero)
    sorted_buffs = sorted(building.buffMissions, key=_sort_buff_easy_first)
    assignments: List[Tuple[str, List[Hero]]] = []
    selected_heroes: List[Hero] = []
    for buff_mission in sorted_buffs:
        candidates = _match_candidates(remaining_pool, buff_mission)
        if len(candidates) < buff_mission.boostConditionCount:
            continue
        selected_for_buff = candidates[:buff_mission.boostConditionCount]
        selected_heroes.extend(selected_for_buff)
        assignments.append((buff_mission.title, selected_for_buff))
        remaining_pool = pop_by_ids(remaining_pool, {h.tokenId for h in selected_for_buff})
        if len(selected_heroes) >= BUILDING_HERO_COUNT:
            break

    # 3) Insert a key hero if possible
    chosen_key_hero = None
    available_key_candidates = [h for h in key_heroes if h.tokenId not in {sel.tokenId for sel in selected_heroes}]
    if available_key_candidates:
        chosen_key_hero = available_key_candidates[0]
        print(f"[PLAN] Selected key hero {chosen_key_hero.tokenId} (grade {chosen_key_hero.grade}) for building '{building.name}'.")
        selected_heroes.append(chosen_key_hero)
        remaining_pool = pop_by_ids(remaining_pool, {chosen_key_hero.tokenId})
    else:
        print(f"[PLAN] WARNING: No available key hero could be inserted for building '{building.name}'.")

    # 4) Fill remaining slots up to 4 heroes
    if len(selected_heroes) < BUILDING_HERO_COUNT:
        fillers = choose_fillers(remaining_pool, BUILDING_HERO_COUNT - len(selected_heroes))
        selected_heroes.extend(fillers)

    # 5) Deduplicate heroes
    unique_selected = {hero.tokenId: hero for hero in selected_heroes}
    selected_heroes = list(unique_selected.values())[:BUILDING_HERO_COUNT]

    # 6) Recalculate buffs with final team
    completed_buffs, buff_titles = _finalize_assignments(selected_heroes, building)
    est_total_points = base_points + base_points * buff_pct_grade * completed_buffs

    return DispatchChoice(
        landId=land_token,
        landName=land_name,
        buildingType=building.buildingType,
        buildingName=building.name,
        grade=building.grade,
        base_points=base_points,
        buffs_possible=completed_buffs,
        buff_percent_each=buff_pct_grade,
        estimated_total_points=est_total_points,
        chosen_heroes=selected_heroes,
        satisfied_buffs_titles=buff_titles,
        reserved_heroes=[],
        reason=f"Dispatch {'with key hero' if chosen_key_hero else 'without key hero'}; completed {completed_buffs} buff(s).",
        buff_requirements=[f"{bm.title}: need={bm.boostConditionCount}" for bm in building.buffMissions],
    )