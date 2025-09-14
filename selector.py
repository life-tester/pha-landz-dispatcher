from typing import List, Tuple
from models import Hero, Building, DispatchChoice
from config import BUILDING_HERO_COUNT, GRADE_POINTS, GRADE_BUFF_PERCENT, GRADE_MAP
from rules import hero_matches, find_all_keys, choose_fillers, pop_by_ids


def _sort_buff_easy_first(mission) -> Tuple[int, int, int]:
    """Sort buffs preferring easier ones:
    - lower required grade first
    - lower buff amount
    - Base before Elite before Genesis before Any
    The tuple ordering ensures stable, predictable selection.
    """
    create_type_preference = {2: 0, 1: 1, 0: 2, -1: 3}.get(mission.createType, 3)
    required_grade = mission.herozGrade if mission.herozGrade != -1 else 0
    return (required_grade, mission.buffAmount, create_type_preference)


def _match_candidates(available_pool: List[Hero], mission) -> List[Hero]:
    """Return heroes that satisfy `mission`, ordered by
    (lower grade, preferred primalType, lower stars, tokenId)."""
    return sorted(
        [hero for hero in available_pool if hero_matches(hero, mission)],
        key=lambda h: (h.grade, {1: 0, 2: 1, 0: 2}.get(h.primalType, 3), h.star, h.tokenId),
    )


def _finalize_assignments(final_selected: List[Hero], building: Building) -> Tuple[int, List[str]]:
    """Recount completed buffs for the final set of 4 heroes and build titles with ids."""
    titles_with_ids: List[str] = []
    completed_count = 0
    for mission in building.buffMissions:
        hits = [hero for hero in final_selected if hero_matches(hero, mission)]
        if len(hits) >= mission.boostConditionCount:
            completed_count += 1
            titles_with_ids.append(
                mission.title + " [" + ", ".join(str(h.tokenId) for h in hits[: mission.boostConditionCount]) + "]"
            )
    return completed_count, titles_with_ids


def evaluate_mission_with_available(
    available_heroes: List[Hero], building: Building, land_token: int, land_name: str
) -> DispatchChoice:
    """Pick 4 distinct heroes to maximize completed buffs while guaranteeing a key hero.
    Logic preserved from the working version; variable names and comments improved for clarity.
    """
    base_points = GRADE_POINTS.get(building.grade, 0)
    buff_percent_for_grade = GRADE_BUFF_PERCENT.get(building.grade, 0.0)

    # Work on a copy of the hero pool so we don't mutate the caller's list.
    working_pool = available_heroes[:]

    # 1) Collect all key heroes (grade >= building.grade).
    key_heroes = find_all_keys(working_pool, building.grade)
    if not key_heroes:
        # No eligible key hero: return a reservation choice with suggested fillers.
        return DispatchChoice(
            landId=land_token,
            landName=land_name,
            buildingType=building.buildingType,
            buildingName=building.name,
            grade=building.grade,
            base_points=base_points,
            buffs_possible=0,
            buff_percent_each=buff_percent_for_grade,
            estimated_total_points=base_points,
            chosen_heroes=[],
            satisfied_buffs_titles=[],
            reserved_heroes=choose_fillers(working_pool, BUILDING_HERO_COUNT),
            reason=f"No eligible key hero (≥ {GRADE_MAP.get(building.grade)}). Reserved for future use.",
        )

    # 2) Try to satisfy buff missions first (without choosing the key yet).
    sorted_missions = sorted(building.buffMissions, key=_sort_buff_easy_first)
    mission_assignments: List[Tuple[str, List[Hero]]] = []  # (mission.title, heroes assigned)
    selected_heroes: List[Hero] = []
    remaining_pool = working_pool[:]

    for mission in sorted_missions:
        candidates = _match_candidates(remaining_pool, mission)
        required_count = mission.boostConditionCount
        if len(candidates) < required_count:
            # Not enough to complete this buff; skip entirely (don't partially consume heroes).
            continue
        take = candidates[:required_count]
        selected_heroes.extend(take)
        mission_assignments.append((mission.title, take))
        remaining_pool = pop_by_ids(remaining_pool, {h.tokenId for h in take})
        if len(selected_heroes) >= BUILDING_HERO_COUNT:
            break

    # 3) Insert a key hero.
    #    If we already have 4 heroes, try replacing one with a key who matches at least one mission.
    #    Otherwise, add a key hero, preferring one that matches a mission constraint.
    chosen_key_hero = None
    selected_ids = {h.tokenId for h in selected_heroes}
    key_candidates = [k for k in key_heroes if k.tokenId not in selected_ids]
    key_preferred = [k for k in key_candidates if any(hero_matches(k, m) for m in building.buffMissions)] or key_candidates

    if len(selected_heroes) >= BUILDING_HERO_COUNT:
        # Need to substitute one hero with a key hero and keep buffs intact if possible.
        for candidate_key in key_preferred:
            replaced = False
            for title, assigned in mission_assignments:
                mission_obj = next((m for m in sorted_missions if m.title == title), None)
                if mission_obj and hero_matches(candidate_key, mission_obj):
                    victim = assigned[0]
                    selected_heroes = [candidate_key if h.tokenId == victim.tokenId else h for h in selected_heroes]
                    assigned[0] = candidate_key
                    chosen_key_hero = candidate_key
                    replaced = True
                    break
            if replaced:
                break
        if chosen_key_hero is None and key_preferred:
            # Could not keep buffs intact; drop one non-critical hero and insert a key.
            needed_ids = {h.tokenId for _, hs in mission_assignments for h in hs}
            victim = next((h for h in selected_heroes if h.tokenId not in needed_ids), None) or selected_heroes[-1]
            chosen_key_hero = key_preferred[0]
            selected_heroes = [h for h in selected_heroes if h.tokenId != victim.tokenId]
            selected_heroes.append(chosen_key_hero)
    else:
        chosen_key_hero = key_preferred[0]
        selected_heroes.append(chosen_key_hero)
        remaining_pool = pop_by_ids(remaining_pool, {chosen_key_hero.tokenId})

    # 4) Fill remaining slots with cheapest fillers up to exactly 4 heroes.
    if len(selected_heroes) < BUILDING_HERO_COUNT:
        fillers = choose_fillers(remaining_pool, BUILDING_HERO_COUNT - len(selected_heroes))
        selected_heroes.extend(fillers)

    # 5) Ensure distinct heroes and limit to exactly 4.
    unique_by_id = {h.tokenId: h for h in selected_heroes}
    selected_heroes = list(unique_by_id.values())[:BUILDING_HERO_COUNT]

    # 6) Recompute completed buffs and total estimation with the final quartet.
    completed_buffs, titles_with_ids = _finalize_assignments(selected_heroes, building)
    estimated_total = base_points + base_points * buff_percent_for_grade * completed_buffs

    # Build human-readable requirement strings (for logs)
    requirements_for_logs: List[str] = []
    for mission in building.buffMissions:
        requirements_for_logs.append(
            f"{mission.title}: createType={mission.createType} "
            f"grade={mission.herozGrade}({mission.herozGradeType}) "
            f"race={mission.herozRace} star={mission.herozStar} "
            f"need={mission.boostConditionCount}"
        )

    reason = (
        f"Dispatch guaranteed with key hero (≥ {GRADE_MAP.get(building.grade)}); "
        f"completed {completed_buffs} buff(s)."
        if chosen_key_hero
        else f"No eligible key hero (≥ {GRADE_MAP.get(building.grade)})."
    )

    return DispatchChoice(
        landId=land_token,
        landName=land_name,
        buildingType=building.buildingType,
        buildingName=building.name,
        grade=building.grade,
        base_points=base_points,
        buffs_possible=completed_buffs,
        buff_percent_each=buff_percent_for_grade,
        estimated_total_points=estimated_total,
        chosen_heroes=selected_heroes,
        satisfied_buffs_titles=titles_with_ids,
        reserved_heroes=[],
        reason=reason,
        buff_requirements=requirements_for_logs,
    )