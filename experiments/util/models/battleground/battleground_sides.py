from abc import abstractmethod
from enum import Enum
import re

from util.wrappers.LLM_wrappers import LLMRequestWrapper
from util.wrappers.API_wrappers import BattlegroundWrapper
from util.logging import Logger
from util.models.game import Game, Role
from util.models.battleground.game_state import GameData
from util.models.prompt_builder import PromptBuilder
from util.models.rules import MUTANT_VALIDATOR_LEVEL_RULES, TEST_RULES


class BattlegroundSide(Game):
    def __init__(self, game_id, agent_username, agent_password, llm_client: LLMRequestWrapper, prompt_builder: PromptBuilder, logger: Logger):
        super().__init__(game_id)

        self._codedefenders_api = BattlegroundWrapper(
            agent_username, agent_password)
        self._llm_client = llm_client
        self._prompt_builder = prompt_builder
        self._logger = logger

        self._chatgpt_conversation = []

        self.join_game()
        self._load_game()

    def _fetch_game_state(self):
        return self._codedefenders_api.fetch(self._game_id)

    def _load_game(self):
        self._game_state_raw = self._fetch_game_state()
        self._game_state = GameData(**self._game_state_raw)

    @abstractmethod
    def join_game(self):
        pass


class SubmittedMutantState(Enum):
    INVALID = 0     # invalid for CD, non-compilable
    STILLBORN = 1   # valid for CD, but killed by defender or duplicate
    ALIVE = 2


class BattlegroundAttacker(BattlegroundSide):
    def __init__(self, game_id, agent_username, agent_password, gpt_client: LLMRequestWrapper, policy: PromptBuilder, logger: Logger):
        super().__init__(game_id, agent_username, agent_password, gpt_client, policy, logger)

        self._restrictions = self._get_restrictions()

    def join_game(self):
        self._codedefenders_api.join(self._game_id, Role.ATTACKER)

    def _get_restrictions(self):
        restrictions_prompt = 'Follow these constraints when making modifications:'
        for level, restrictions in MUTANT_VALIDATOR_LEVEL_RULES.items():
            restrictions_prompt += f'{restrictions}'
            if level == self._game_state.mutant_validator_level:
                return restrictions_prompt

    def _parse_response(self, response):
        if (response['rejectReason'] == 'DUPLICATE_MUTANT_FOUND') or (response['success'] and (response['mutant']['state'] == 'KILLED')):
            return SubmittedMutantState.STILLBORN
        if response['success'] == False:
            return SubmittedMutantState.INVALID

        return SubmittedMutantState.ALIVE

    def make_submission(self):
        self._load_game()
        new_game_state = None
        system_prompt, user_prompt = self._prompt_builder.generate_prompt(
            self._game_state, self._restrictions)
        llm_response = self._llm_client.get_response(
            system_prompt, user_prompt, temperature=1.0)

        llm_response = llm_response.replace(r'\u', r'\\u')
        mutant = re.sub(r'(\x00|\\u0000|\\0)', '', llm_response)
        mutant = re.sub(r"```(?:java)?\n?|\n?```", "", mutant).strip()

        codedefenders_response = self._codedefenders_api.submit_mutant(
            self._game_id, mutant)
        mutant_state = self._parse_response(codedefenders_response)

        if codedefenders_response['success']:
            new_game_state = self._fetch_game_state()

        return mutant_state, system_prompt, user_prompt, mutant, llm_response, codedefenders_response, self._game_state_raw, new_game_state


class SubmittedTestState(Enum):
    INVALID = 0    # invalid for CD, non-compilable
    MISS = 1       # valid for CD, but did not kill the targeted mutant
    KILL = 2


class BattlegroundDefender(BattlegroundSide):
    def __init__(self, game_id, agent_username, agent_password, gpt_client: LLMRequestWrapper, prompt_builder: PromptBuilder, class_alias: str, logger: Logger):
        super().__init__(game_id, agent_username,
                         agent_password, gpt_client, prompt_builder, logger)

        self._restrictions = self._get_restrictions()
        self.survivors = []

        self._class_alias = class_alias

    def join_game(self):
        self._codedefenders_api.join(self._game_id, Role.DEFENDER)

    def _get_restrictions(self):
        restrictions_prompt = 'Follow these constraints when creating your test:'
        for level, restrictions in TEST_RULES.items():
            restrictions_prompt += f'{restrictions} '
            if level == 'BASE':
                return restrictions_prompt

    def target_mutant(self):
        alive_mutants = [
            mutant for mutant in self._game_state.mutants if mutant.state == 'ALIVE']

        targeted_mutant_id = next(
            (mutant.mutant_id for mutant in alive_mutants if mutant.mutant_id not in self.survivors), None)

        return targeted_mutant_id

    def pick_mutants(self):
        targeted_mutant_id = self.target_mutant()

        while targeted_mutant_id:
            print(f'Killing mutant: {targeted_mutant_id}...')
            mutant_id = self.make_submission(targeted_mutant_id)
            if mutant_id:
                self.survivors.append(mutant_id)
            targeted_mutant_id = self.target_mutant()

    def _parse_response(self, response, targeted_mutant_id):
        if response['success'] == False:
            return SubmittedTestState.INVALID
        if targeted_mutant_id in [mutant for mutant in response['test']['killedMutants']]:
            return SubmittedTestState.KILL

        return SubmittedTestState.MISS

    def make_submission(self, mutant_id):
        self._load_game()
        system_prompt, user_prompt = self._prompt_builder.generate_prompt(
            self._game_state, self._restrictions, mutant_id, self._class_alias)
        llm_response = self._llm_client.get_response(
            system_prompt, user_prompt, temperature=1.0)

        test_template = f'import org.junit.Test;import static org.junit.Assert.*;import static org.hamcrest.MatcherAssert.assertThat;import static org.hamcrest.Matchers.*;public class Test{self._class_alias} {{@Test(timeout = 4000)public void test() throws Throwable {{// test here!}}}}'

        llm_response = llm_response.replace(
            r'\u', r'\\u').replace('\0', '').replace('\\0', '')
        submission = re.sub(r'// test here!', llm_response, test_template)
        submission = re.sub(r"```(?:java)?\n?|\n?```", "", submission).strip()

        codedefenders_response = self._codedefenders_api.submit_test(
            self._game_id, submission)
        test_state = self._parse_response(codedefenders_response, mutant_id)

        new_game_state = None
        if codedefenders_response['success']:
            new_game_state = self._fetch_game_state()

        return test_state, system_prompt, user_prompt, submission, llm_response, codedefenders_response, self._game_state_raw, new_game_state
