from typing import Dict


# Mapping of grade values to human-readable names
GRADE_MAP: Dict[int, str] = {0: "Common", 1: "Rare", 2: "Epic", 3: "Legendary", 4: "Mythical"}


# Base points for each grade
GRADE_POINTS: Dict[int, int] = {0: 100, 1: 150, 2: 250, 3: 500, 4: 1000}


# Buff percentage bonus per grade
GRADE_BUFF_PERCENT: Dict[int, float] = {0: 0.10, 1: 0.20, 2: 0.30, 3: 0.40, 4: 0.50}


# Number of heroes required per building dispatch
BUILDING_HERO_COUNT: int = 4


# Priority order of missions by grade
MISSION_PRIORITY = [4, 3, 2, 1, 0]


# API Endpoints
API_BASE_URL = "https://dapp-backend.pixelheroes.io"
DISPATCH_ENDPOINT = "/landz/dispatchHeroZReg"
CLAIM_ENDPOINT = "/landz/dispatchReward"
PRIMAL_TAG = "PRIMAL"
PRIMAL_SUFFIX = "0"