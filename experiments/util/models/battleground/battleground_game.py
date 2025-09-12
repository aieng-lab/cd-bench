from datetime import datetime, timezone
from util.wrappers.LLM_wrappers import LLMRequestWrapper
from util.wrappers.API_wrappers import BattlegroundWrapper
from util.logging import Logger
from util.models.battleground.battleground_sides import BattlegroundAttacker, BattlegroundDefender, SubmittedMutantState, SubmittedTestState
from util.models.game import Game
from util.models.prompt_builder import AttackerPromptBuilder, DefenderPromptBuilder


class BattlegroundGameSettings:
    def __init__(self,
                 class_alias: str, mutant_validator_level: str, duration_minutes: int, level: str,
                 turns: int,
                 attacker_mutants_per_turn: int,
                 attacker_max_compile_attempts: int, attacker_max_stillborn_mutants: int,
                 defender_max_compile_attempts: int, defender_max_kill_attempts: int,
                 attacker_model_name: str = None, attacker_model_family: str = None,
                 defender_model_name: str = None, defender_model_family: str = None):

        self.class_alias = class_alias
        self.mutant_validator_level = mutant_validator_level
        self.duration_minutes = duration_minutes
        self.level = level

        self.turns = turns

        self.attacker_mutants_per_turn = attacker_mutants_per_turn

        self.attacker_max_compile_attempts = attacker_max_compile_attempts
        self.attacker_max_stillborn_mutants = attacker_max_stillborn_mutants

        self.defender_max_compile_attempts = defender_max_compile_attempts
        self.defender_max_kill_attempts = defender_max_kill_attempts

        self.attacker_model_name = attacker_model_name
        self.attacker_model_family = attacker_model_family
        self.defender_model_name = defender_model_name
        self.defender_model_family = defender_model_family

    def to_json(self):
        return {
            'class_alias': self.class_alias,
            'mutant_validator_level': self.mutant_validator_level,
            'duration_minutes': self.duration_minutes,
            'level': self.level,
            'turns': self.turns,
            'attacker_mutants_per_turn': self.attacker_mutants_per_turn,
            'attacker_max_compile_attempts': self.attacker_max_compile_attempts,
            'attacker_max_stillborn_mutants': self.attacker_max_stillborn_mutants,
            'defender_max_compile_attempts': self.defender_max_compile_attempts,
            'defender_max_kill_attempts': self.defender_max_kill_attempts,
            'attacker_model_name': self.attacker_model_name,
            'attacker_model_family': self.attacker_model_family,
            'defender_model_name': self.defender_model_name,
            'defender_model_family': self.defender_model_family
        }

    @staticmethod
    def from_json(json_data):
        return BattlegroundGameSettings(
            class_alias=json_data['class_alias'],
            mutant_validator_level=json_data['mutant_validator_level'],
            duration_minutes=json_data['duration_minutes'],
            level=json_data['level'],
            turns=json_data['turns'],
            attacker_mutants_per_turn=json_data['attacker_mutants_per_turn'],
            attacker_max_compile_attempts=json_data['attacker_max_compile_attempts'],
            attacker_max_stillborn_mutants=json_data['attacker_max_stillborn_mutants'],
            defender_max_compile_attempts=json_data['defender_max_compile_attempts'],
            defender_max_kill_attempts=json_data['defender_max_kill_attempts'],
            attacker_model_name=json_data['attacker_model_name'],
            attacker_model_family=json_data['attacker_model_family'],
            defender_model_name=json_data['defender_model_name'],
            defender_model_family=json_data['defender_model_family']
        )


class BattlegroundGame(Game):
    def __init__(self, game_id, attacker: BattlegroundAttacker, defender: BattlegroundDefender, battleground_game_api: BattlegroundWrapper, game_settings: BattlegroundGameSettings, logger: Logger):
        super().__init__(game_id)

        self._attacker = attacker
        self._defender = defender

        self._battleground_game_api = battleground_game_api

        self._turns = game_settings.turns
        self._attacker_mutants_per_turn = game_settings.attacker_mutants_per_turn

        self._attacker_max_compile_attempts = game_settings.attacker_max_compile_attempts
        self._attacker_max_stillborn_mutants = game_settings.attacker_max_stillborn_mutants

        self._defender_max_compile_attempts = game_settings.defender_max_compile_attempts
        self._defender_max_kill_attempts = game_settings.defender_max_kill_attempts

        self._logger = logger

    @classmethod
    def create(cls,
               game_settings: BattlegroundGameSettings,
               attacker_username: str,
               attacker_password: str,
               attacker_prompt_builder: AttackerPromptBuilder,
               attacker_llm_client: LLMRequestWrapper,
               defender_username: str,
               defender_password: str,
               defender_prompt_builder: DefenderPromptBuilder,
               defender_llm_client: LLMRequestWrapper,
               battleground_game_api: BattlegroundWrapper,
               logger: Logger) -> 'BattlegroundGame':
        game_id = battleground_game_api.create(game_settings.class_alias,
                                               mutant_validator_level=game_settings.mutant_validator_level,
                                               duration_minutes=game_settings.duration_minutes,
                                               level=game_settings.level)['gameId']

        attacker = BattlegroundAttacker(
            game_id, attacker_username, attacker_password, attacker_llm_client, attacker_prompt_builder, logger)
        defender = BattlegroundDefender(game_id, defender_username, defender_password,
                                        defender_llm_client, defender_prompt_builder, game_settings.class_alias, logger)

        return cls(game_id, attacker, defender, battleground_game_api, game_settings, logger)

    def start(self):
        self._battleground_game_api.start(self._game_id)

    def end(self):
        self._battleground_game_api.end(self._game_id)

    def play(self):
        self.start()

        for turn in range(self._turns):
            print(f'Turn {turn+1}')

            mutants = self.attacker_turn(turn + 1, self._attacker_mutants_per_turn,
                                         self._attacker_max_compile_attempts, self._attacker_max_stillborn_mutants)
            self.defender_turn(
                turn + 1, mutants, self._defender_max_compile_attempts, self._defender_max_kill_attempts)

            self._logger.save_logs()

    def __log_attacker(self, state: int, turn: int, objective: str, attempt: int, submission: int, system_prompt: str, user_prompt: str, mutant: str, llm_response: dict, codedefenders_response: dict, last_game_state: dict, new_game_state: dict):
        self._logger.log_submission(game_id=self._game_id,
                                    side='attacker',
                                    model_name=self._attacker._llm_client._model,
                                    state=state,
                                    turn=turn,
                                    objective=objective,
                                    attempt=attempt,
                                    submission=submission,
                                    date=datetime.now(timezone.utc),
                                    last_game_state=last_game_state,
                                    new_game_state=new_game_state,
                                    system_prompt=system_prompt,
                                    user_prompt=user_prompt,
                                    context=None,
                                    llm_response=llm_response,
                                    codedefenders_submission=mutant,
                                    codedefenders_response=codedefenders_response)

    def attacker_turn(self, turn: int, mutants_per_turn: int, attacker_max_compile_attempts: int, attacker_max_stillborn_mutants: int):
        created_mutants = []

        for mutant_index in range(mutants_per_turn):
            for stillborn_attempt_index in range(attacker_max_stillborn_mutants):
                for compile_attempt_index in range(attacker_max_compile_attempts):
                    mutant_state, system_prompt, user_prompt, codedefenders_submission, llm_response, codedefenders_response, last_game_state, new_game_state = self._attacker.make_submission()
                    self.__log_attacker(mutant_state.value, turn, mutant_index+1, stillborn_attempt_index+1, compile_attempt_index+1,
                                        system_prompt, user_prompt, codedefenders_submission, llm_response, codedefenders_response,
                                        last_game_state, new_game_state)

                    print(
                        f'Game Id: {self._game_id}. Turn {turn}. Mutant {mutant_index+1}. Attempt {stillborn_attempt_index+1} Submission {compile_attempt_index+1}. State: {mutant_state.name}.')

                    if mutant_state != SubmittedMutantState.INVALID:
                        break
                if mutant_state == SubmittedMutantState.ALIVE:
                    created_mutants.append(
                        codedefenders_response['mutant']['mutantId'])
                    break

        return created_mutants

    def __log_defender(self, state: int, turn: int, objective: str, attempt: int, submission: int, system_prompt: str, user_prompt: str, mutant: str, llm_response: dict, codedefenders_response: dict, last_game_state: dict, new_game_state: dict):
        self._logger.log_submission(game_id=self._game_id,
                                    side='defender',
                                    model_name=self._defender._llm_client._model,
                                    state=state,
                                    turn=turn,
                                    objective=objective,
                                    attempt=attempt,
                                    submission=submission,
                                    date=datetime.now(timezone.utc),
                                    last_game_state=last_game_state,
                                    new_game_state=new_game_state,
                                    system_prompt=system_prompt,
                                    user_prompt=user_prompt,
                                    context=None,
                                    llm_response=llm_response,
                                    codedefenders_submission=mutant,
                                    codedefenders_response=codedefenders_response)

    def defender_turn(self, turn: int, mutants, defender_max_compile_attempts: int, defender_max_kill_attempts: int):
        for mutant_id in mutants:
            for kill_attempt in range(defender_max_kill_attempts):
                for compile_attempt in range(defender_max_compile_attempts):
                    test_state, system_prompt, user_prompt, codedefenders_submission, llm_response, codedefenders_response, last_game_state, new_game_state = self._defender.make_submission(
                        mutant_id)
                    self.__log_defender(test_state.value, turn, mutant_id, kill_attempt+1, compile_attempt+1,
                                        system_prompt, user_prompt, codedefenders_submission, llm_response, codedefenders_response,
                                        last_game_state, new_game_state)

                    print(
                        f'Game Id: {self._game_id}. Turn {turn}. Targeted mutant {mutant_id}. Kill attempt {kill_attempt+1}. Submission {compile_attempt+1}. State: {test_state.name}.')

                    if test_state != SubmittedTestState.INVALID:
                        break
                if test_state == SubmittedTestState.KILL:
                    break
