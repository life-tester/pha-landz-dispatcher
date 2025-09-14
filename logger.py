from models import Plan, Hero, DispatchChoice
from config import GRADE_MAP
from rules import race_name, CREATE_TYPE_NAME


def _hero_detail(hero: Hero) -> str:
    return f"{hero.tokenId}({race_name(hero.race)}, {CREATE_TYPE_NAME.get(hero.primalType,'?')}, G{hero.grade}, S{hero.star})"


def _fmt_list(heroes):
    return ", ".join(_hero_detail(h) for h in heroes) if heroes else "—"


def _fmt_buffs(titles, count, pct):
    if count <= 0:
        return "—"
    label = f"{count} x {int(pct*100)}%"
    return label + (" [" + "; ".join(titles[:count]) + "]" if titles else "")


def log_plan(plan: Plan):
    print("=== Dispatch Plan ===")
    if not plan.choices:
        print("(no options)")
        return
    for index, choice in enumerate(plan.choices, 1):
        grade_name = GRADE_MAP.get(choice.grade, str(choice.grade))
        buffs = _fmt_buffs(choice.satisfied_buffs_titles, choice.buffs_possible, choice.buff_percent_each)
        chosen = _fmt_list(choice.chosen_heroes) if choice.chosen_heroes else "(reserved only)"
        reserved = _fmt_list(choice.reserved_heroes)
        print(
            f"{index:02d}. - #{choice.landId} | {choice.buildingName} | Grade={grade_name} | "
            f"Base={choice.base_points} | Buffs={buffs} | Est.Total={choice.estimated_total_points:.1f} | "
            f"Chosen=[{chosen}] | Reserved=[{reserved}] | {choice.reason}"
        )
        if isinstance(choice, DispatchChoice) and choice.buff_requirements:
            print("    Requirements:")
            for req in choice.buff_requirements:
                print(f"      - {req}")