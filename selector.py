from typing import List, Tuple, Optional

from models import Hero, Building, DispatchChoice
from config import BUILDING_HERO_COUNT, GRADE_POINTS, GRADE_BUFF_PERCENT, GRADE_MAP
from rules import hero_matches, find_all_keys, choose_fillers, pop_by_ids


# -----------------------------
# Helpers de ordenação/custo
# -----------------------------
_PRIMAL_PREF = {1: 0, 2: 1, 0: 2}  # Base < Elite < Genesis (mantido)


def _hero_cost_key(h: Hero) -> Tuple[int, int, int, int]:
    """Menor custo: menor grade, Base antes de Elite/Genesis, menor star e tokenId."""
    return (h.grade, _PRIMAL_PREF.get(h.primalType, 3), h.star, h.tokenId)


def _sort_buff_easy_first(mission) -> Tuple[int, int, int]:
    """Ordem estável usada apenas para logs e fallback.
    - menor grade exigida primeiro
    - menor buffAmount
    - Base antes de Elite antes de Genesis antes de Any
    """
    create_type_preference = {2: 0, 1: 1, 0: 2, -1: 3}.get(mission.createType, 3)
    required_grade = mission.herozGrade if mission.herozGrade != -1 else 0
    return (required_grade, mission.buffAmount, create_type_preference)


def _match_candidates(pool: List[Hero], mission) -> List[Hero]:
    return sorted(
        [h for h in pool if hero_matches(h, mission)],
        key=_hero_cost_key,
    )


def _finalize_assignments(final_selected: List[Hero], building: Building) -> Tuple[int, List[str]]:
    titles_with_ids: List[str] = []
    completed_count = 0
    for mission in building.buffMissions:
        hits = [hero for hero in final_selected if hero_matches(hero, mission)]
        if len(hits) >= mission.boostConditionCount:
            completed_count += 1
            titles_with_ids.append(
                mission.title
                + " ["
                + ", ".join(str(h.tokenId) for h in hits[: mission.boostConditionCount])
                + "]"
            )
    return completed_count, titles_with_ids


# -----------------------------
# Núcleo: busca pequena e determinística
# -----------------------------

def _build_candidate_pool(available: List[Hero], building: Building, cap_per_mission: int = 8) -> List[Hero]:
    """Une candidatos relevantes às missões + keys + fillers baratos.
    Mantém o conjunto pequeno para permitir backtracking leve.
    """
    pool: List[Hero] = []

    # Candidatos por missão (prioridade por custo)
    for m in building.buffMissions:
        pool.extend(_match_candidates(available, m)[:cap_per_mission])

    # Keys sempre entram
    keys = find_all_keys(available, building.grade)
    pool.extend(keys)

    # Alguns fillers baratos para completar times
    need_fillers = max(0, BUILDING_HERO_COUNT)
    pool.extend(choose_fillers(available, need_fillers))

    # Dedup por tokenId preservando a primeira ocorrência (mais barata)
    uniq = {}
    for h in pool:
        if h.tokenId not in uniq:
            uniq[h.tokenId] = h
    pool_dedup = list(uniq.values())

    # Ordena priorizando: keys que ajudam missões > demais candidatos de missão > outros keys > fillers
    def priority(h: Hero) -> Tuple[int, Tuple[int, int, int, int]]:
        h_matches_any = any(hero_matches(h, m) for m in building.buffMissions)
        is_key = h in keys
        # menor é melhor; valores negativos dão prioridade
        if is_key and h_matches_any:
            p = 0
        elif h_matches_any:
            p = 1
        elif is_key:
            p = 2
        else:
            p = 3
        return (p, _hero_cost_key(h))

    return sorted(pool_dedup, key=priority)


def _needs_after_take(needs: List[int], h: Hero, missions) -> List[int]:
    new_needs = needs[:]
    for i, m in enumerate(missions):
        if new_needs[i] > 0 and hero_matches(h, m):
            new_needs[i] = max(0, new_needs[i] - 1)
    return new_needs


def _backtrack_complete_with_key(
    key_hero: Hero,
    candidates: List[Hero],
    missions,
    max_extra: int,
) -> Optional[List[Hero]]:
    """Tenta completar TODAS as missões usando o key + até max_extra heróis.
    Permite sobreposição (um herói pode contar para múltiplas missões).
    Retorna somente os extras (sem o key)."""
    needs = [m.boostConditionCount for m in missions]
    # Aplica o key
    needs = _needs_after_take(needs, key_hero, missions)

    best: Optional[List[Hero]] = None

    # pré-cálculo: para poda rápida, o máximo que podemos reduzir com o restante
    def feasible(needs_left: List[int], start_idx: int, left_slots: int) -> bool:
        # checagem simples: se a soma das necessidades excede o número de slots * 2, dificilmente cabe.
        # (cada herói pode no máximo cobrir as duas missões)
        if sum(needs_left) > left_slots * 2:
            return False
        # também verifica se existe ao menos "needs_left[i]" candidatos restantes que batem cada missão
        for i, m in enumerate(missions):
            if needs_left[i] <= 0:
                continue
            count_match = 0
            for h in candidates[start_idx:]:
                if hero_matches(h, m):
                    count_match += 1
            if count_match < needs_left[i]:
                return False
        return True

    chosen: List[Hero] = []

    def bt(idx: int, needs_left: List[int]):
        nonlocal best, chosen
        if all(n <= 0 for n in needs_left):
            # solução encontrada; escolhe a mais barata/menor
            cand = chosen[:]
            if best is None or (len(cand), [ _hero_cost_key(x) for x in sorted(cand, key=_hero_cost_key) ]) < (
                len(best), [ _hero_cost_key(x) for x in sorted(best, key=_hero_cost_key) ]
            ):
                best = cand
            return
        if idx >= len(candidates):
            return
        if len(chosen) >= max_extra:
            return
        left_slots = max_extra - len(chosen)
        if not feasible(needs_left, idx, left_slots):
            return

        # Escolha 1: pegar o candidato atual
        h = candidates[idx]
        if h.tokenId != key_hero.tokenId and h not in chosen:
            chosen.append(h)
            bt(idx + 1, _needs_after_take(needs_left, h, missions))
            chosen.pop()

        # Escolha 2: pular
        bt(idx + 1, needs_left)

    bt(0, needs)
    return best


def _try_both_missions(
    key_hero: Hero,
    pool: List[Hero],
    missions,
) -> Optional[List[Hero]]:
    # Considera apenas candidatos que ajudam pelo menos 1 missão (mantém busca enxuta)
    mission_helpers = [h for h in pool if any(hero_matches(h, m) for m in missions) and h.tokenId != key_hero.tokenId]
    mission_helpers = sorted(mission_helpers, key=_hero_cost_key)[:16]

    extras = _backtrack_complete_with_key(key_hero, mission_helpers, missions, max_extra=3)
    if extras is None:
        return None
    selection = [key_hero] + extras
    # Completa para 4 com fillers baratos
    remaining = [h for h in pool if h.tokenId not in {x.tokenId for x in selection}]
    fillers = choose_fillers(remaining, BUILDING_HERO_COUNT - len(selection))
    return selection + fillers


def _try_single_mission(
    key_hero: Hero,
    pool: List[Hero],
    missions,
) -> Optional[List[Hero]]:
    # Escolhe a missão de MAIOR buffAmount primeiro (critério do usuário quando só dá para uma)
    missions_sorted = sorted(missions, key=lambda m: (-m.buffAmount, ) + _sort_buff_easy_first(m))

    for m in missions_sorted:
        need = m.boostConditionCount
        need_after_key = need - (1 if hero_matches(key_hero, m) else 0)
        if need_after_key < 0:
            need_after_key = 0

        if need_after_key == 0:
            chosen = [key_hero]
        else:
            cands = [h for h in pool if hero_matches(h, m) and h.tokenId != key_hero.tokenId]
            cands = sorted(cands, key=_hero_cost_key)
            if len(cands) < need_after_key:
                continue  # não dá para completar esta missão
            chosen = [key_hero] + cands[:need_after_key]

        # completa para 4 com fillers
        remaining = [h for h in pool if h.tokenId not in {x.tokenId for x in chosen}]
        fillers = choose_fillers(remaining, BUILDING_HERO_COUNT - len(chosen))
        return chosen + fillers

    return None


# -----------------------------
# Função pública
# -----------------------------

def evaluate_mission_with_available(
    available_heroes: List[Hero],
    building: Building,
    land_token: int,
    land_name: str,
) -> DispatchChoice:
    """Seleciona exatamente 4 heróis maximizando buffs completos SEM consumo parcial.

    Estratégia:
      1) exige ao menos 1 key hero (grade >= da building) no conjunto final;
      2) tenta completar DUAS missões simultaneamente com sobreposição (o key pode contar);
      3) senão, completa UMA missão (priorizando maior buffAmount), com o key contando quando possível;
      4) se nada disso for possível, envia key + fillers baratos;
      5) custo sempre: menor grade, Base < Elite < Genesis, menor star, menor tokenId.
    """
    base_points = GRADE_POINTS.get(building.grade, 0)
    buff_percent_for_grade = GRADE_BUFF_PERCENT.get(building.grade, 0.0)

    # Copiamos o pool para não mutar o chamador
    pool = available_heroes[:]

    # 1) Keys
    key_heroes = find_all_keys(pool, building.grade)
    if not key_heroes:
        # Sem key: apenas reserva fillers
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
            reserved_heroes=choose_fillers(pool, BUILDING_HERO_COUNT),
            reason=f"No eligible key hero (≥ {GRADE_MAP.get(building.grade)}). Reserved for future use.",
        )

    # 2) Constrói um pool enxuto e ordenado por prioridade/custo
    cand_pool = _build_candidate_pool(pool, building)

    # Tenta primeiro com keys que ajudam alguma missão
    preferred_keys = [k for k in key_heroes if any(hero_matches(k, m) for m in building.buffMissions)]
    other_keys = [k for k in key_heroes if k not in preferred_keys]
    try_keys = sorted(preferred_keys, key=_hero_cost_key) + sorted(other_keys, key=_hero_cost_key)

    final_selection: Optional[List[Hero]] = None

    # 3) Tentar completar DUAS missões
    for key_h in try_keys:
        both = _try_both_missions(key_h, cand_pool, building.buffMissions)
        if both is not None:
            final_selection = both
            break

    # 4) Tentar UMA missão (priorizando maior buff)
    if final_selection is None:
        for key_h in try_keys:
            one = _try_single_mission(key_h, cand_pool, building.buffMissions)
            if one is not None:
                final_selection = one
                break

    # 5) Se ainda não deu, key + fillers
    if final_selection is None:
        key_h = try_keys[0]
        remaining = [h for h in cand_pool if h.tokenId != key_h.tokenId]
        fillers = choose_fillers(remaining, BUILDING_HERO_COUNT - 1)
        final_selection = [key_h] + fillers

    # Sanitiza: distintos e exatamente 4
    uniq = {}
    for h in final_selection:
        uniq[h.tokenId] = h
    final_selection = list(uniq.values())[:BUILDING_HERO_COUNT]

    # Reconta buffs e total estimado
    completed_buffs, titles_with_ids = _finalize_assignments(final_selection, building)
    estimated_total = base_points + base_points * buff_percent_for_grade * completed_buffs

    # Requisitos para logs/debug
    requirements_for_logs: List[str] = []
    for mission in building.buffMissions:
        requirements_for_logs.append(
            f"{mission.title}: createType={mission.createType} "
            f"grade={mission.herozGrade}({mission.herozGradeType}) "
            f"race={mission.herozRace} star={mission.herozStar} "
            f"need={mission.boostConditionCount}"
        )

    reason = (
        f"Dispatch guaranteed with key hero (≥ {GRADE_MAP.get(building.grade)}); completed {completed_buffs} buff(s)."
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
        chosen_heroes=final_selection,
        satisfied_buffs_titles=titles_with_ids,
        reserved_heroes=[],
        reason=reason,
        buff_requirements=requirements_for_logs,
    )
