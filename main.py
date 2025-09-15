import argparse
import sys
from api import Api, InvalidTokenError
from planner import build_plan
from logger import log_plan
from dispatcher import run_dispatch_single


def _validate_token_format(token: str) -> bool:
    """Checks if token has a valid JWT-like format (3 parts separated by '.')"""
    return token and len(token.split(".")) == 3


def _refresh_state(api: Api):
    heroes = api.get_heroes()
    lands = api.get_lands()
    for land in lands:
        land.buildings = api.get_buildings(land.tokenId)
    return heroes, lands


def main():
    parser = argparse.ArgumentParser(description="Pixel Heroes Adventure Dispatcher")
    parser.add_argument("--token", type=str, required=True, help="Bearer token for Pixel Heroes API")
    parser.add_argument("--region", type=int, default=1, help="Region ID: 1=Meta Toy City, 2=Ludo City")
    parser.add_argument("--confirm", action="store_true", help="Execute dispatches (default is dry-run)")
    parser.add_argument("--all", action="store_true", help="In confirm mode, dispatch ALL available missions")
    parser.add_argument("--max-dispatches", type=int, default=999999, help="Upper bound for total dispatches")
    parser.add_argument("--claim-first", action="store_true", help="Claim rewards before planning/dispatching")
    args = parser.parse_args()

    if not _validate_token_format(args.token):
        print("❌ Invalid Bearer token format. It should look like: xxxxx.yyyyy.zzzzz")
        sys.exit(1)

    try:
        api = Api(args.token, region=args.region)
        print("[ROUND 1] Fetching current state…")
        heroes, lands = _refresh_state(api)
    except InvalidTokenError as e:
        print(f"❌ {e}")
        print("🔑 Please check your Bearer token and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    if args.claim_first:
        for land in lands:
            any_claim = any(b.pendingReward for b in land.buildings)
            if any_claim:
                print(f"[CLAIM] Attempting claim for land={land.tokenId}")
                try:
                    res = api.claim(land.tokenId)
                    status = res.get("header", {}).get("status", 0)
                    msg = (res.get("header", {}).get("message") or "").strip()
                    if status == 200:
                        print(f"[CLAIM] ✅ SUCCESS → {msg}")
                    else:
                        print(f"[CLAIM] ❌ FAILED (status {status}) → {msg}")
                except InvalidTokenError:
                    print("❌ Your Bearer token expired during claim. Please refresh and try again.")
                    sys.exit(1)

        heroes, lands = _refresh_state(api)

    plan = build_plan(api, lands, heroes)
    log_plan(plan)

    if not args.confirm:
        print("[DRY-RUN] Finished. No dispatch executed.")
        return

    total_sent = 0
    to_run = [c for c in plan.choices if c.chosen_heroes]
    if not args.all:
        to_run = to_run[:1]

    for choice in to_run:
        ok = run_dispatch_single(api, choice, max_retries=3, delay=5)
        if not ok:
            print("[HALT] Stopping due to failed dispatch after retries.")
            return
        total_sent += 1
        if total_sent >= args.max_dispatches:
            break

    print(f"[CONFIRM] Finished. Total successful dispatches: {total_sent}")


if __name__ == "__main__":
    main()
