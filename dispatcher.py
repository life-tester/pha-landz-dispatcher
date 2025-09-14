import time
import json
from typing import Tuple
from models import DispatchChoice
from api import Api
from config import PRIMAL_TAG, PRIMAL_SUFFIX

ALREADY_MSG_KEYS = (
    "already being dispatched",
    "already dispatched",
    "already in progress",
)


def _payload(choice: DispatchChoice) -> dict:
    hero_list = [f"{h.tokenId}-{PRIMAL_TAG}-{PRIMAL_SUFFIX}" for h in choice.chosen_heroes]
    return {
        "heroZTokenIds": ",".join(hero_list),
        "landZTokenId": str(choice.landId),
        "buildingType": choice.buildingType,
    }


def _server_in_progress(api: Api, land_id: int, building_type: int) -> Tuple[bool, int, bool]:
    """Check server state to avoid dispatching to a busy building."""
    try:
        buildings = api.get_buildings(land_id)
    except Exception as exc:
        print(f"[API] ⚠️ Preflight check failed: {exc}")
        return False, 0, False
    for building in buildings:
        if int(building.buildingType) == int(building_type):
            return bool(building.herozList), (len(building.herozList) if building.herozList else 0), bool(building.pendingReward)
    return False, 0, False


def run_dispatch_single(api: Api, choice: DispatchChoice, max_retries: int = 3, delay: int = 5) -> bool:
    """Dispatch a single building choice with exponential backoff retries."""
    in_progress, count, pending = _server_in_progress(api, choice.landId, choice.buildingType)
    if in_progress or pending:
        reason = "pendingReward=true" if pending else f"herozList has {count} hero(s)"
        print(f"[SKIP] Building already busy on server → land={choice.landId} btype={choice.buildingType} ({reason})")
        return True

    attempts = 0
    while attempts < max_retries:
        attempts += 1
        payload = _payload(choice)
        print(f"[API] Dispatching… payload={json.dumps(payload)}")

        response = api.dispatch(choice.landId, choice.buildingType, choice.chosen_heroes)
        status = response.get("header", {}).get("status", 0)
        message = (response.get("header", {}).get("message") or "").strip()
        print(f"[API] Response status={status}, message={message}")

        if status == 200:
            print("[API] ✅ SUCCESS")
            return True

        if status == 201:
            lower = message.lower()
            if any(key in lower for key in ALREADY_MSG_KEYS):
                print("[API] ⚠️ Already in progress at server. Skipping as success.")
                return True
            else:
                print(f"[API] ❌ Error (201) → {message} | attempt {attempts}/{max_retries}")
        else:
            print(f"[API] ❌ Error (status {status}) → {message} | attempt {attempts}/{max_retries}")

        if attempts >= max_retries:
            print("[API] ❌ Giving up after retries.")
            return False
        wait_time = delay * (2 ** (attempts - 1))
        print(f"[API] Retrying in {wait_time}s…")
        time.sleep(wait_time)

    return False