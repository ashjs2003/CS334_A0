from dataclasses import dataclass
from typing import Optional, Dict, Tuple
import numpy as np


# =========================
# Data types
# =========================
@dataclass
class Player:
    name: str
    node: int
    wealth: float = 0.0
    teleport_allowed: bool = False
    vision_radius: float = np.inf

@dataclass
class Resource:
    rid: int
    node: int
    value: int
    bias: str

@dataclass
class FaithParameters:
    teleport_access: Optional[Dict[str, bool]] = None
    spawn_bias: Optional[Dict[str, float]] = None
    location_restriction: Optional[Dict[str, Tuple]] = None
    vision_radius: Optional[Dict[str, float]] = None
    inactive_windows: Optional[Dict[str, Tuple[int, int]]] = None
