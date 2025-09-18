from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Hero:
    tokenId: int
    grade: int
    name: str = ""
    race: int = -1
    star: int = 0
    primalType: int = -1  # 0 = Genesis, 1 = Base, 2 = Elite
    createType: int = -1  # espelho de primalType para logs
    uid: Optional[int] = None

@dataclass
class BuffMission:
    title: str
    createType: int
    herozGrade: int
    herozGradeType: int
    herozRace: int
    herozRaceType: int
    herozStar: int
    herozStarType: int
    boostConditionCount: int
    buffAmount: int

@dataclass
class Building:
    buildingType: int
    grade: int
    name: str
    herozList: List[Hero]
    pendingReward: bool
    buffMissions: List[BuffMission]
    remainCount: int
    rewardAmount: int

@dataclass
class LandZ:
    tokenId: int
    name: str
    buildings: List[Building] = field(default_factory=list)

@dataclass
class DispatchChoice:
    landId: int
    landName: str
    buildingType: int
    buildingName: str
    grade: int
    base_points: int
    buffs_possible: int
    buff_percent_each: float
    estimated_total_points: float
    chosen_heroes: List[Hero]
    satisfied_buffs_titles: List[str]
    reserved_heroes: List[Hero]
    reason: str
    buff_requirements: List[str] = field(default_factory=list)

@dataclass
class Plan:
    choices: List[DispatchChoice]