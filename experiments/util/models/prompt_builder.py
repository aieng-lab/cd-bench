from abc import ABC, abstractmethod
from enum import Enum

from util.models.battleground.game_state import GameData


class AttackerPolicyEnum(Enum):
    METHOD = 0
    LEAST_COVERAGE = 1


class PromptBuilder(ABC):
    def __init__(self, prompt, tests_covered_lines: bool, tests_code: bool, mutated_lines: bool, mutants_code: bool):
        self.prompt = prompt

        self.tests_covered_lines = tests_covered_lines
        self.tests_code = tests_code

        self.mutated_lines = mutated_lines
        self.mutants_code = mutants_code


class AttackerPromptBuilder(PromptBuilder):
    def __init__(self, prompt, tests_covered_lines=False, tests_code=False, mutants=False, mutants_code=False):
        super().__init__(prompt, tests_covered_lines, tests_code, mutants, mutants_code)

    def generate_prompt(self, game_state: GameData, restrictions):
        system_prompt = f'{self.prompt} {restrictions}'

        user_prompt = f'The original class:\n\n{game_state.mark_mutated_code()}'

        if self.tests_covered_lines:
            user_prompt += f'\n\nThe following lines are covered by the tests: {game_state.get_lines_tested()}'

        if self.tests_code:
            user_prompt += '\n\nYour code will be tested against the tests below, try to avoid being spotted:\n'
            for test in game_state.tests:
                user_prompt += test.code + '\n\n'

        if self.mutated_lines:
            user_prompt += f'\n\nThe following lines are already mutated: {game_state.get_lines_mutated()}'

        if self.mutants_code:
            user_prompt += '\n\nThe following mutants\' diffs are available:\n'
            for mutant in game_state.mutants:
                user_prompt += mutant.diff + '\n\n'

        return (system_prompt, user_prompt)


class DefenderPromptBuilder(PromptBuilder):
    def __init__(self, prompt, tests_covered_lines=False, tests_code=False, mutants=False, mutants_code=False):
        super().__init__(prompt, tests_covered_lines, tests_code, mutants, mutants_code)

    def generate_prompt(self, game_state: GameData, restrictions, entity_id, class_name):
        system_prompt = f'{self.prompt} {restrictions}'

        diff = next(
            (mutant.diff for mutant in game_state.mutants if mutant.mutant_id == entity_id), None)

        test_template = 'import org.junit.Test; import static org.junit.Assert.*; import static org.hamcrest.MatcherAssert.assertThat; import static org.hamcrest.Matchers.*; public class Test' + \
            class_name + \
            ' {     @Test(timeout = 4000)     public void test() throws Throwable {         // test here!     }}'

        user_prompt = f'The original class:\n\n{game_state.cut.code}\n\nThe diff that is applied to the original class:\n\n{diff}\n\nThe test template:\n\n{test_template}'

        return (system_prompt, user_prompt)
