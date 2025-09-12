import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from abc import ABC, abstractmethod

from openai import OpenAI
import anthropic
import time
import random


class LLMPromptResponse:
    def __init__(self, prompt, response):
        self.prompt = prompt
        self.response = response


class LLMRequestWrapper(ABC):
    def __init__(self, model):
        self._model = model

    @abstractmethod
    def get_response(self, system, prompt, context=None, temperature=0.3):
        pass


class ChatGPTRequestWrapper(LLMRequestWrapper):
    def __init__(self, model, api_key):
        super().__init__(model)
        self._api_key = api_key
        self._client = OpenAI(api_key=self._api_key)

    def get_response(self, system, prompt, context=None, temperature=0.3):
        messages = []

        messages.append(
            {
                'role': 'system',
                'content': system,
            })

        if context and len(context) > 0:
            for turn in context:
                if turn.prompt != None:
                    messages.append({
                        'role': 'user',
                        'content': turn.prompt,
                    })
                if turn.response != None:
                    messages.append({
                        'role': 'assistant',
                        'content': turn.response,
                    })

        messages.append(
            {
                'role': 'user',
                'content': prompt,
            })
        response = self._client.chat.completions.create(
            messages=messages,
            model=self._model,
            temperature=temperature,
            max_tokens=4096)
        return response.choices[0].message.content


class ClaudeRequestWrapper(LLMRequestWrapper):
    def __init__(self, model, api_key):
        super().__init__(model)

        self._client = anthropic.Anthropic(api_key=api_key)

    def get_response(self, system_prompt, user_prompt, context=None, temperature=0.3):
        messages = []

        if context and len(context) > 0:
            for turn in context:
                if turn.prompt != None:
                    messages.append({
                        'role': 'user',
                        'content': turn.prompt,
                    })
                if turn.response != None:
                    messages.append({
                        'role': 'assistant',
                        'content': turn.response,
                    })

        messages.append(
            {
                'role': 'user',
                'content': user_prompt,
            })

        max_retries = 200
        for attempt in range(max_retries):
            try:
                response = self._client.messages.create(
                    system=system_prompt,
                    model=self._model,
                    max_tokens=4096,
                    temperature=temperature,
                    messages=messages
                )
                return response.content[0].text

            except anthropic.RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = (20 * attempt) + random.uniform(0, 1)
                    print(
                        f"Rate limit hit. Waiting {wait_time:.2f} seconds before retry {attempt + 2}...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise

            except anthropic.APIError as e:
                print(f"Anthropic API error: {e}")
                if e.status_code == 500:
                    continue


class GeminiRequestWrapper(LLMRequestWrapper):
    def __init__(self, model, api_key):
        super().__init__(model)
        genai.configure(api_key=api_key)

    def get_response(self, system_prompt, user_prompt, context=None, temperature=0.3):
        model_instance = genai.GenerativeModel(
            self._model,
            system_instruction=system_prompt
        )
        conversation_history = []

        if context:
            for turn in context:
                if turn.prompt is not None:
                    conversation_history.append(
                        {'role': 'user', 'parts': [turn.prompt]})
                if turn.response is not None:
                    conversation_history.append(
                        {'role': 'model', 'parts': [turn.response]})

        conversation_history.append({'role': 'user', 'parts': [user_prompt]})

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=4096
        )

        max_retries = 200
        for attempt in range(max_retries):
            try:
                response = model_instance.generate_content(
                    contents=conversation_history,
                    generation_config=generation_config
                )

                if response.prompt_feedback.block_reason:
                    print(
                        f"Gemini prompt was blocked: {response.prompt_feedback.block_reason.name}")
                    return response.prompt_feedback.block_reason.name

                if response.candidates and response.candidates[0].finish_reason.name not in ["STOP", "MAX_TOKENS"]:
                    print(
                        f"Gemini response generation stopped for reason: {response.candidates[0].finish_reason.name}")
                    return response.candidates[0].finish_reason.name

                if not response.parts:
                    print(
                        f"Gemini response is empty. Finish reason: {response.candidates[0].finish_reason.name}")
                    return response.candidates[0].finish_reason.name

                return response.text
            except google_exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    wait_time = (20 * attempt) + random.uniform(0, 1)
                    print(
                        f"Gemini rate limit hit. Waiting {wait_time:.2f} seconds before retry {attempt + 1}...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(
                        f"Gemini API rate limit exceeded after multiple retries: {e}")
                    raise
            except google_exceptions.InternalServerError as e:
                if attempt < max_retries - 1:
                    wait_time = (20 * attempt) + random.uniform(0, 1)
                    print(
                        f"Gemini internal error (500). Waiting {wait_time:.2f} seconds before retry {attempt + 1}...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(
                        f"Gemini internal error persisted after multiple retries: {e}")
                    raise
            except Exception as e:
                msg = str(e)
                if "500" in msg and "internal" in msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = (20 * attempt) + random.uniform(0, 1)
                        print(
                            f"Gemini internal error (500) encountered. Waiting {wait_time:.2f} seconds before retry {attempt + 1}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(
                            f"Gemini API internal error persisted after multiple retries: {e}")
                        raise
                print(f"An unexpected error occurred with Gemini API: {e}")
                raise
