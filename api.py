from typing import List, Dict, Any
import requests
from models import Hero, LandZ, Building, BuffMission
from config import API_BASE_URL, DISPATCH_ENDPOINT, CLAIM_ENDPOINT, PRIMAL_TAG, PRIMAL_SUFFIX


class InvalidTokenError(Exception):
    """Raised when the provided Bearer token is invalid or unauthorized."""
    pass


class Api:
    def __init__(self, token: str, region: int = 1):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Region-Id": str(region),
        })

    def _handle_response(self, response):
        if response.status_code == 401:
            raise InvalidTokenError("Unauthorized: Bearer token is invalid or expired.")
        response.raise_for_status()
        return response

    def get_heroes(self) -> List[Hero]:
        url = f"{API_BASE_URL}/landz/dispatchHeroZList"
        payload = {
            "listType": 1,
            "generation": "PRIMAL",
            "grade": [0, 1, 2, 3, 4],
            "primalType": [0, 1, 2],
            "race": list(range(11)),
            "starStart": 0,
            "starEnd": 3,
        }
        r = self.session.post(url, json=payload)
        self._handle_response(r)
        body = r.json().get("body", [])
        heroes: List[Hero] = []
        for h in body:
            primal = int(h.get("primalType", -1))
            heroes.append(
                Hero(
                    tokenId=int(h["tokenId"]),
                    grade=int(h.get("grade", -1)),
                    name=h.get("name", ""),
                    race=int(h.get("race", -1)),
                    star=int(h.get("star", 0)),
                    primalType=primal,
                    createType=primal,
                    uid=h.get("uid"),
                )
            )
        return heroes

    def get_lands(self) -> List[LandZ]:
        url = f"{API_BASE_URL}/landz/dispatchList"
        r = self.session.get(url)
        self._handle_response(r)
        data = r.json().get("body", {})
        arr = data.get("dispatchLandZList", data if isinstance(data, list) else [])
        lands: List[LandZ] = []
        for x in arr:
            lands.append(LandZ(tokenId=int(x["tokenId"]), name=x.get("name", "")))
        return lands

    def get_buildings(self, land_token: int) -> List[Building]:
        url = f"{API_BASE_URL}/landz/dispatchBuildingInfo"
        r = self.session.post(url, json={"tokenId": str(land_token)})
        self._handle_response(r)
        arr = r.json().get("body", [])
        buildings: List[Building] = []
        for b in arr:
            buff_missions = []
            for m in b.get("missions", []):
                need = int(m.get("boostConditionCount", m.get("boostConditionType", 0)))
                buff_missions.append(
                    BuffMission(
                        title=m.get("title", ""),
                        createType=int(m.get("createType", -1)),
                        herozGrade=int(m.get("herozGrade", -1)),
                        herozGradeType=int(m.get("herozGradeType", -1)),
                        herozRace=int(m.get("herozRace", -1)),
                        herozRaceType=int(m.get("herozRaceType", -1)),
                        herozStar=int(m.get("herozStar", -1)),
                        herozStarType=int(m.get("herozStarType", -1)),
                        boostConditionCount=need,
                        buffAmount=int(m.get("buffAmount", 0)),
                    )
                )
            heroz_list: List[Hero] = []
            for h in b.get("herozList", []):
                heroz_list.append(
                    Hero(
                        tokenId=int(h.get("tokenId")),
                        grade=int(h.get("grade", 0)),
                        name=h.get("name", ""),
                        race=int(h.get("race", -1)),
                        star=int(h.get("star", 0)),
                        primalType=-1,
                        createType=-1,
                        uid=h.get("uid"),
                    )
                )
            buildings.append(
                Building(
                    buildingType=int(b.get("buildingType")),
                    grade=int(b.get("grade", 0)),
                    name=b.get("name", ""),
                    herozList=heroz_list,
                    pendingReward=bool(b.get("pendingReward", False)),
                    buffMissions=buff_missions,
                    remainCount=int(b.get("remainCount", 0)),
                    rewardAmount=int(b.get("rewardAmount", 0)),
                )
            )
        return buildings

    def dispatch(self, land_id: int, building_type: int, heroes: List[Hero]) -> Dict[str, Any]:
        hero_str = ",".join(f"{h.tokenId}-{PRIMAL_TAG}-{PRIMAL_SUFFIX}" for h in heroes)
        payload = {"heroZTokenIds": hero_str, "landZTokenId": str(land_id), "buildingType": building_type}
        r = self.session.post(f"{API_BASE_URL}{DISPATCH_ENDPOINT}", json=payload)
        self._handle_response(r)
        return r.json()

    def claim(self, land_id: int) -> Dict[str, Any]:
        payload = {"tokenId": str(land_id)}
        r = self.session.post(f"{API_BASE_URL}{CLAIM_ENDPOINT}", json=payload)
        self._handle_response(r)
        return r.json()
