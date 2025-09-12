from abc import ABC
from enum import Enum


class Role(Enum):
    DEFENDER = 0
    ATTACKER = 1
    OBSERVER = 2


class Game(ABC):
    def __init__(self, game_id):
        super().__init__()
        self._game_id = game_id


class MeleeGame(Game):
    def __init__(self, game_id):
        super().__init__(game_id)

        pass
