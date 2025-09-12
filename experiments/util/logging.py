import json
import psycopg2


class Logger:
    def __init__(self, user, password, dbname="logs", host="localhost", port="5432"):
        self._dbname = dbname
        self._user = user
        self._password = password
        self._host = host
        self._port = port

        self._create_submissions_table()
        self._create_games_table()

        self.log = []

    def log_game(self, game_id, date, class_alias, attacker, defender,
                 turns, attacker_mutants_per_turn,
                 attacker_max_stillborn_mutants, attacker_max_compile_attempts,
                 defender_max_kill_attempts, defender_max_compile_attempts):
        try:
            with psycopg2.connect(
                dbname=self._dbname,
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port
            ) as connection:
                connection.autocommit = True
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO battleground_games (
                            game_id,
                            date,
                            class_alias,
                            attacker,
                            defender,
                            turns,
                            attacker_mutants_per_turn,
                            attacker_max_stillborn_mutants,
                            attacker_max_compile_attempts,
                            defender_max_kill_attempts,
                            defender_max_compile_attempts
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        game_id,
                        date,
                        class_alias,
                        attacker,
                        defender,
                        turns,
                        attacker_mutants_per_turn,
                        attacker_max_stillborn_mutants,
                        attacker_max_compile_attempts,
                        defender_max_kill_attempts,
                        defender_max_compile_attempts
                    ))
        except Exception as e:
            print("Error:", e)

    def log_submission(self, game_id, side, model_name, state, turn, objective, attempt, submission, date, last_game_state, system_prompt, user_prompt, context, llm_response, codedefenders_submission, codedefenders_response, new_game_state=None):
        self.log.append((game_id, side, model_name, state, turn, objective, attempt, submission, date, json.dumps(last_game_state), system_prompt, user_prompt,
                        context, llm_response, codedefenders_submission, json.dumps(codedefenders_response), json.dumps(new_game_state) if new_game_state else None))

    def _create_submissions_table(self):
        create_table_query = """
            CREATE TABLE IF NOT EXISTS submissions (
                id SERIAL PRIMARY KEY,
                game_id TEXT,
                side TEXT,
                model_name TEXT,
                state INT,
                turn INT,
                objective TEXT,
                attempt INT,
                submission INT,
                date TIMESTAMP,
                last_game_state TEXT,
                system_prompt TEXT,
                user_prompt TEXT,
                context TEXT,
                llm_response TEXT,                
                codedefenders_submission TEXT,
                codedefenders_response TEXT,
                new_game_state TEXT
            )
            """

        try:
            with psycopg2.connect(
                dbname=self._dbname,
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port
            ) as connection:
                connection.autocommit = True
                with connection.cursor() as cursor:
                    cursor.execute(create_table_query)
        except Exception as e:
            print("Error:", e)

    def _create_games_table(self):
        create_table_query = """
            CREATE TABLE IF NOT EXISTS battleground_games (
                id SERIAL PRIMARY KEY,
                game_id TEXT,
                date TIMESTAMP,
                class_alias TEXT,
                attacker TEXT,
                defender TEXT,
                turns INT,
                attacker_mutants_per_turn INT,
                attacker_max_stillborn_mutants INT,
                attacker_max_compile_attempts INT,
                defender_max_kill_attempts INT,
                defender_max_compile_attempts INT
            )
            """

        try:
            with psycopg2.connect(
                dbname=self._dbname,
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port
            ) as connection:
                connection.autocommit = True
                with connection.cursor() as cursor:
                    cursor.execute(create_table_query)
        except Exception as e:
            print("Error:", e)

    def save_logs(self):
        try:
            with psycopg2.connect(
                dbname=self._dbname,
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port
            ) as connection:
                connection.autocommit = True
                with connection.cursor() as cursor:
                    for entry in self.log:
                        cursor.execute(
                            """
                            INSERT INTO submissions (
                                game_id,
                                side,
                                model_name,
                                state,
                                turn,
                                objective,
                                attempt,
                                submission,
                                date,
                                last_game_state,
                                system_prompt,
                                user_prompt,
                                context,
                                llm_response,
                                codedefenders_submission,
                                codedefenders_response,
                                new_game_state
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            entry
                        )
        except Exception as e:
            print("Error:", e)
            print(entry)
            raise e

        self.log = []
