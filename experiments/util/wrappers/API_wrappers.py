import requests
import base64
from abc import ABC

from util.models.game import Role


class CodeDefendersAPIWrapperBase(ABC):
    def __init__(self, username, user_password, host_url='http://localhost:8080/'):
        self._username = username
        self._userPassword = user_password
        self._host_url = host_url

        credentials = f"{self._username}:{self._userPassword}"
        self._encoded_credentials = base64.b64encode(
            credentials.encode()).decode()


class BattlegroundWrapper(CodeDefendersAPIWrapperBase):
    def __init__(self, username, user_password, host_url='http://localhost:8080/', api='llm-api/battleground/'):
        super().__init__(username, user_password, host_url)
        self._api = api

    def list(self):
        url = self._host_url + self._api + 'list'

        headers = {"Authorization": f"Basic {self._encoded_credentials}"}

        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}:")
            print(response.text)

    def fetch(self, game_id):
        url = self._host_url + self._api + 'game'

        params = {"gameId": game_id}
        headers = {"Authorization": f"Basic {self._encoded_credentials}"}

        response = requests.get(
            url, params=params, headers=headers, verify=False)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}:")
            print(response.text)

    def create(self,
               class_alias,
               with_tests=False,
               with_mutants=False,
               max_assertions_per_test=2,
               automatic_equivalence_trigger=0,
               mutant_validator_level='moderate',
               creator_role='observer',
               duration_minutes=60,
               level='easy'):
        url = self._host_url + self._api + 'create'

        params = {
            "classAlias": class_alias,
            "withTests": with_tests,
            "withMutants": with_mutants,
            "maxAssertionsPerTest": max_assertions_per_test,
            "automaticEquivalenceTrigger": automatic_equivalence_trigger,
            "mutantValidatorLevel": mutant_validator_level,
            "creatorRole": creator_role,
            "durationMinutes": duration_minutes,
            "level": level
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encoded_credentials}"
        }

        response = requests.post(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}:")
            print(response.text)

    def join(self, game_id, role: Role):
        url = self._host_url + self._api + 'join'

        params = {
            "gameId": game_id,
            "role": role.name
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encoded_credentials}"
        }

        response = requests.post(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}:")
            print(response.text)

    def start(self, game_id):
        url = self._host_url + self._api + 'start'

        params = {
            "gameId": game_id
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encoded_credentials}"
        }

        response = requests.post(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}:")
            print(response.text)

    def end(self, game_id):
        url = self._host_url + self._api + 'end'

        params = {
            "gameId": game_id
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encoded_credentials}"
        }

        response = requests.post(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}:")
            print(response.text)

    def __submit_code(self, game_id, code, endpoint):
        url = self._host_url + self._api + endpoint

        data = {
            'gameId': game_id,
            'code': code
        }
        headers = {
            "Authorization": f"Basic {self._encoded_credentials}"
        }

        response = requests.post(url, data=data, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Request failed with status code {response.status_code}:")
            print(response.text)

    def submit_test(self, game_id, code):
        return self.__submit_code(game_id, code, 'submit-test')

    def submit_mutant(self, game_id, code):
        return self.__submit_code(game_id, code, 'submit-mutant')
