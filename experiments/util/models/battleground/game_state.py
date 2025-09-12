class Cut:
    def __init__(self, classId, alias, name, code, dependencies, testingFramework, assertionLibrary):
        self.class_id = classId
        self.alias = alias
        self.name = name
        self.code = code
        self.dependencies = dependencies
        self.testing_framework = testingFramework
        self.assertion_library = assertionLibrary

    def get_total_lines(self):
        return len(self.code.split('\n'))

    def code_with_line_numbers(self):
        return '\r\n'.join([f'{line}//Line {i+1}' for i, line in enumerate(self.code.split('\r\n'))])

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(
            classId=data["class_id"],
            alias=data["alias"],
            name=data["name"],
            code=data["code"],
            dependencies=data["dependencies"],
            testingFramework=data["testing_framework"],
            assertionLibrary=data["assertion_library"]
        )


class Player:
    def __init__(self, playerId, userId, isSystemPlayer, role, points):
        self.player_id = playerId
        self.user_id = userId
        self.is_system_player = isSystemPlayer
        self.role = role
        self.points = points

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class Test:
    def __init__(self, testId, playerId, canView, code, score, linesCovered, coveredMutants, killedMutants):
        self.test_id = testId
        self.player_id = playerId
        self.can_view = canView
        self.code = code
        self.score = score
        self.lines_covered = linesCovered
        self.covered_mutants = coveredMutants
        self.killed_mutants = killedMutants

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class Mutant:
    def __init__(self, mutantId, playerId, canView, diff, modifiedLines, score, state, covered, canMarkEquivalent, killedByTestId, killMessage):
        self.mutant_id = mutantId
        self.player_id = playerId
        self.can_view = canView
        self.diff = diff
        self.modified_lines = modifiedLines
        self.score = score
        self.state = state
        self.covered = covered
        self.can_mark_equivalent = canMarkEquivalent
        self.killed_by_test_id = killedByTestId
        self.kill_message = killMessage

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class HistoryEvent:
    def __init__(self, eventId, playerId, timestamp, type, eventType=None):
        self.event_id = eventId
        self.player_id = playerId
        self.event_type = eventType
        self.timestamp = timestamp
        self.type = type

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class GameData:
    def __init__(self, cut, players, mutants, tests, history, pendingEquivalentMutant, startTime, duration, level, mutantValidatorLevel, maxAssertionsPerTest, automaticEquivalenceThreshold):
        self.cut = Cut(**cut)
        self.players = [Player(**player) for player in players]
        self.mutants = [Mutant(**mutant) for mutant in mutants]
        self.tests = [Test(**test) for test in tests]
        self.history = [HistoryEvent(**event) for event in history]
        self.pending_equivalent_mutant = pendingEquivalentMutant
        self.start_time = startTime
        self.duration = duration
        self.level = level
        self.mutant_validator_level = mutantValidatorLevel
        self.max_assertions_per_test = maxAssertionsPerTest
        self.automatic_equivalence_threshold = automaticEquivalenceThreshold

    def get_data_for_defender(self, tests: bool, mutants: bool):
        return self.cut.code, self.tests if tests else None, self.mutants if mutants else None

    def get_data_for_attacker(self, tests: bool, mutants: bool):
        return self.cut.code, self.tests if tests else None, self.mutants if mutants else None

    def get_lines_tested(self):
        return list(set(line for test in self.tests for line in test.lines_covered))

    def get_lines_mutated(self):
        return list(set(line for mutant in self.mutants for line in mutant.modified_lines))

    def mark_mutated_code(self):
        lines = self.cut.code.split("\r\n")

        marked_lines = [
            f"{line.rstrip()} // This line is already mutated, changing it again is forbidden" if (
                index + 1) in self.get_lines_mutated() else line
            for index, line in enumerate(lines)
        ]

        return "\r\n".join(marked_lines)

    def to_dict(self):
        return {
            "cut": self.cut.to_dict(),
            "players": [player.to_dict() for player in self.players],
            "mutants": [mutant.to_dict() for mutant in self.mutants],
            "tests": [test.to_dict() for test in self.tests],
            "history": [event.to_dict() for event in self.history],
            "pending_equivalent_mutant": self.pending_equivalent_mutant,
            "start_time": self.start_time,
            "duration": self.duration,
            "level": self.level,
            "mutant_validator_level": self.mutant_validator_level,
            "max_assertions_per_test": self.max_assertions_per_test,
            "automatic_equivalence_threshold": self.automatic_equivalence_threshold
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            cut=data["cut"],
            players=data["players"],
            mutants=data["mutants"],
            tests=data["tests"],
            history=data["history"],
            pendingEquivalentMutant=data["pending_equivalent_mutant"],
            startTime=data["start_time"],
            duration=data["duration"],
            level=data["level"],
            mutantValidatorLevel=data["mutant_validator_level"],
            maxAssertionsPerTest=data["max_assertions_per_test"],
            automaticEquivalenceThreshold=data["automatic_equivalence_threshold"]
        )
