from typing import List, Dict, Any
import requests
from models import Hero, LandZ, Building, BuffMission
from config import API_BASE_URL, DISPATCH_ENDPOINT, CLAIM_ENDPOINT, PRIMAL_TAG, PRIMAL_SUFFIX

class Api:
    def __init__(self, token: str, region: int = 1):
        # Create a session with default headers for all requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Region-Id": str(region),  # 1 = Meta Toy City, 2 = Ludo City
        })

    def get_heroes(self) -> List[Hero]:
        """Fetch the list of available heroes for dispatch.
        *Robusto contra lista vazia ou formato inesperado.*
        """
        url = f"{API_BASE_URL}/landz/dispatchHeroZList"
        payload = {
            "listType": 1,
            "generation": "PRIMAL",
            "grade": [0, 1, 2, 3, 4],
            "primalType": [0, 1, 2],  # 0 = Genesis, 1 = Base, 2 = Elite
            "race": list(range(11)),
            "starStart": 0,
            "starEnd": 3,
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()

        body = response.json().get("body", [])
        if not isinstance(body, list):
            print("[WARN] dispatchHeroZList unexpected format; using empty list.")
            return []
        if not body:
            print("[INFO] dispatchHeroZList returned empty; no heroes available.")
            return []

        hero_list: List[Hero] = []
        for hero_data in body:
            try:
                primal = int(hero_data.get("primalType", -1))
                hero_list.append(Hero(
                    tokenId=int(hero_data["tokenId"]),
                    grade=int(hero_data.get("grade", -1)),
                    name=hero_data.get("name", ""),
                    race=int(hero_data.get("race", -1)),
                    star=int(hero_data.get("star", 0)),
                    primalType=primal,
                    createType=primal,
                    uid=hero_data.get("uid"),
                ))
            except (KeyError, ValueError) as e:
                print(f"[WARN] Skipping invalid hero entry: {hero_data} ({e})")
        return hero_list

    def get_lands(self) -> List[LandZ]:
        """Fetch the list of lands and their token IDs."""
        url = f"{API_BASE_URL}/landz/dispatchList"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json().get("body", {})
        land_array = data.get("dispatchLandZList", data if isinstance(data, list) else [])
        lands: List[LandZ] = []
        for land_data in land_array:
            lands.append(LandZ(tokenId=int(land_data["tokenId"]), name=land_data.get("name", "")))
        return lands

    def get_buildings(self, land_token: int) -> List[Building]:
        """Fetch all buildings for a given land."""
        url = f"{API_BASE_URL}/landz/dispatchBuildingInfo"
        response = self.session.post(url, json={"tokenId": str(land_token)})
        response.raise_for_status()
        building_array = response.json().get("body", [])
        buildings: List[Building] = []
        for building_data in building_array:
            # Parse buff missions for each building
            buff_missions = []
            for mission_data in building_data.get("missions", []):
                need = int(mission_data.get("boostConditionCount", mission_data.get("boostConditionType", 0)))
                buff_missions.append(BuffMission(
                    title=mission_data.get("title", ""),
                    createType=int(mission_data.get("createType", -1)),
                    herozGrade=int(mission_data.get("herozGrade", -1)),
                    herozGradeType=int(mission_data.get("herozGradeType", -1)),
                    herozRace=int(mission_data.get("herozRace", -1)),
                    herozRaceType=int(mission_data.get("herozRaceType", -1)),
                    herozStar=int(mission_data.get("herozStar", -1)),
                    herozStarType=int(mission_data.get("herozStarType", -1)),
                    boostConditionCount=need,
                    buffAmount=int(mission_data.get("buffAmount", 0)),
                ))

            # Parse heroes already assigned to this building
            hero_list: List[Hero] = []
            for hero_data in building_data.get("herozList", []):
                hero_list.append(Hero(
                    tokenId=int(hero_data.get("tokenId")),
                    grade=int(hero_data.get("grade", 0)),
                    name=hero_data.get("name", ""),
                    race=int(hero_data.get("race", -1)),
                    star=int(hero_data.get("star", 0)),
                    primalType=-1,
                    createType=-1,
                    uid=hero_data.get("uid"),
                ))

            # Append building to result list
            buildings.append(Building(
                buildingType=int(building_data.get("buildingType")),
                grade=int(building_data.get("grade", 0)),
                name=building_data.get("name", ""),
                herozList=hero_list,
                pendingReward=bool(building_data.get("pendingReward", False)),
                buffMissions=buff_missions,
                remainCount=int(building_data.get("remainCount", 0)),
                rewardAmount=int(building_data.get("rewardAmount", 0)),
            ))
        return buildings

    def dispatch(self, land_id: int, building_type: int, heroes: List[Hero]) -> Dict[str, Any]:
        """Send a dispatch request with the chosen heroes."""
        hero_str = ",".join(f"{hero.tokenId}-{PRIMAL_TAG}-{PRIMAL_SUFFIX}" for hero in heroes)
        payload = {"heroZTokenIds": hero_str, "landZTokenId": str(land_id), "buildingType": building_type}
        response = self.session.post(f"{API_BASE_URL}{DISPATCH_ENDPOINT}", json=payload)
        try:
            return response.json()
        except Exception:
            return {"raw": response.text, "status_code": response.status_code}

    def claim(self, land_id: int) -> Dict[str, Any]:
        """Claim rewards for a specific land."""
        payload = {"tokenId": str(land_id)}
        response = self.session.post(f"{API_BASE_URL}{CLAIM_ENDPOINT}", json=payload)
        try:
            return response.json()
        except Exception:
            return {"raw": response.text, "status_code": response.status_code}