from util.models.battleground.battleground_game import BattlegroundGameSettings
from util.models.battleground.battleground_game import BattlegroundGame
from datetime import datetime, timezone
import json
import argparse

from util.wrappers.API_wrappers import BattlegroundWrapper
from util.models.prompt_builder import AttackerPromptBuilder, DefenderPromptBuilder
from util.wrappers.LLM_wrappers import ChatGPTRequestWrapper, ClaudeRequestWrapper, GeminiRequestWrapper
from util.logging import Logger


setups_path = 'resources/setups/'

with open('config/llm_api_keys.json') as json_file:
    llm_apikeys = json.load(json_file)

with open('config/codedefenders_users.json') as json_file:
    code_defenders_credentials = json.load(json_file)

with open('config/postgres_user.json') as json_file:
    database_credentials = json.load(json_file)

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "logs"
DB_USER = database_credentials["user"]
DB_PASSWORD = database_credentials["password"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, required=True)
    return parser.parse_args()


def get_prompt_builders():
    prompt = "Modify the behavior of a single method in the given class to introduce a mutant. Select a method that has not been mutated yet, considering the lines of code that have already been altered in other versions. Ensure the mutation introduces a subtle bug that changes behavior without completely breaking functionality.\n\nEnsure that the mutation results in a realistic bug that subtly alters the behavior of the method while keeping it syntactically valid. Return just raw code of the entire class without any formatting markers.\n\n"
    attack_prompt_builder = AttackerPromptBuilder(prompt)

    prompt = 'Generate the body of the test() method for a Java unit test that detects the bug introduced by the provided diff. Return only the body of the test method, excluding the test() method signature and surrounding {} brackets. You are not allowed to give anything else but the code of the test method. Return just raw code without any markdown or formatting markers.'
    defender_prompt_builder = DefenderPromptBuilder(prompt)

    return attack_prompt_builder, defender_prompt_builder


def get_llm_client(model_name, model_family):
    if model_family == 'openai':
        return ChatGPTRequestWrapper(model_name, llm_apikeys['openai'])
    elif model_family == 'anthropic':
        return ClaudeRequestWrapper(model_name, llm_apikeys['anthropic'])
    elif model_family == 'google':
        return GeminiRequestWrapper(model_name, llm_apikeys['google'])
    else:
        raise ValueError(f"Unsupported model family: {model_family}")


def run_experiment(setup_id):
    try:
        with open(f'{setups_path}{setup_id}.json', 'r') as file:
            game_settings = BattlegroundGameSettings.from_json(json.load(file))

        logger = Logger(user=DB_USER, password=DB_PASSWORD,
                        host=DB_HOST, port=DB_PORT, dbname=DB_NAME)

        host_wrapper = BattlegroundWrapper(
            'host', code_defenders_credentials['host'])

        attack_prompt_builder, defender_prompt_builder = get_prompt_builders()
        attacker_llm = get_llm_client(
            game_settings.attacker_model_name, game_settings.attacker_model_family)
        defender_llm = get_llm_client(
            game_settings.defender_model_name, game_settings.defender_model_family)

        game = BattlegroundGame.create(
            game_settings,
            attacker_username='attacker',
            attacker_password=code_defenders_credentials['attacker'],
            attacker_prompt_builder=attack_prompt_builder,
            attacker_llm_client=attacker_llm,
            defender_username='defender',
            defender_password=code_defenders_credentials['defender'],
            defender_prompt_builder=defender_prompt_builder,
            defender_llm_client=defender_llm,
            battleground_game_api=host_wrapper,
            logger=logger)

        print(
            f"Starting game {game._game_id} with attacker {attacker_llm._model} and defender {defender_llm._model}. Class: {game_settings.class_alias}.")

        game.play()

        logger.log_game(game._game_id,
                        datetime.now(timezone.utc),
                        game_settings.class_alias,
                        attacker_llm._model,
                        defender_llm._model,
                        game_settings.turns,
                        game_settings.attacker_mutants_per_turn,
                        game_settings.attacker_max_stillborn_mutants,
                        game_settings.attacker_max_compile_attempts,
                        game_settings.defender_max_kill_attempts,
                        game_settings.defender_max_compile_attempts)
    except Exception as e:
        print(f"Exception occurred: {e}")
        print(
            f"Error in game {game._game_id} with attacker {attacker_llm._model} and defender {defender_llm._model}. Class: {game_settings.class_alias}.")


if __name__ == "__main__":
    args = parse_args()

    run_experiment(args.id)
