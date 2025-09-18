from typing import List, Dict
from models import Hero, BuffMission

# Human names for races (aid for logging)
RACE_MAP: Dict[int, str] = {
    0: "Bear", 1: "Monkey", 2: "Rabbit", 3: "Squirrel", 4: "Horse",
    5: "Badger", 6: "Tiger", 7: "Cat", 8: "Dog", 9: "Raccoon", 10: "Fox",
}

# Human names for primal/create types (aid for logging)
CREATE_TYPE_NAME: Dict[int, str] = {0: "Genesis", 1: "Base", 2: "Elite", -1: "Any"}

# Convert mission.createType -> hero.primalType
MISSION_CT_TO_PRIMAL: Dict[int, int] = {0: 0, 1: 2, 2: 1, -1: -1}


def race_name(race_id: int) -> str:
    return RACE_MAP.get(race_id, str(race_id))


def create_type_name(type_id: int) -> str:
    return CREATE_TYPE_NAME.get(type_id, str(type_id))


def _primal_rank(primal_type: int) -> int:
    """Ranking para desempate em 'barateza'.
    Preferir Base(1) < Elite(2) < Genesis(0) < desconhecido.
    """
    return {1: 0, 2: 1, 0: 2}.get(primal_type, 3)


def hero_matches(hero: Hero, mission: BuffMission) -> bool:
    """Return True if `hero` satisfies all constraints of `mission`."""
    # createType / primalType check
    required_primal = MISSION_CT_TO_PRIMAL.get(mission.createType, -1)
    if required_primal != -1 and hero.primalType != required_primal:
        return False

    # grade check
    if mission.herozGrade != -1:
        if mission.herozGradeType == 1 and hero.grade < mission.herozGrade:
            return False
        if mission.herozGradeType != 1 and hero.grade != mission.herozGrade:
            return False

    # race check
    if mission.herozRace != -1 and hero.race != mission.herozRace:
        return False

    # star check
    if mission.herozStar != -1:
        if mission.herozStarType == 1 and hero.star < mission.herozStar:
            return False
        if mission.herozStarType != 1 and hero.star != mission.herozStar:
            return False

    return True


def find_all_keys(available_heroes: List[Hero], minimum_grade: int) -> List[Hero]:
    """Heroes que podem ser key (grade >= minimum_grade),
    ordenados por **menor grade primeiro**, depois primal mais barato, menos estrelas, tokenId.
    """
    return sorted(
        [hero for hero in available_heroes if hero.grade >= minimum_grade],
        key=lambda h: (h.grade, _primal_rank(h.primalType), h.star, h.tokenId),
    )


def choose_fillers(available_heroes: List[Hero], count: int) -> List[Hero]:
    """Preenche com heróis mais baratos (mesmo critério de ordenação)."""
    return sorted(
        available_heroes,
        key=lambda h: (h.grade, _primal_rank(h.primalType), h.star, h.tokenId),
    )[:count]


def pop_by_ids(pool: List[Hero], token_ids: set[int]) -> List[Hero]:
    """Remove do pool heróis com tokenId em `token_ids`."""
    return [hero for hero in pool if hero.tokenId not in token_ids]