"""Сервис классификации упавшего теста: текст падения -> проверенный FailureClassification.

Только логика: собрать сообщения, вызвать клиент, проверить ответ. DTO, промпт и клиент — импортом.
"""

import json

from pydantic import ValidationError

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.dto.classification import FailureClassification
from qa_agents.errors import ClassificationError
from qa_agents.prompts.classifier_prompt import FEW_SHOT_EXAMPLES, SYSTEM_PROMPT

# Сколько раз переспрашивать модель, если она вернула невалидный JSON.
MAX_ATTEMPTS = 2


def build_messages(failure_text: str) -> list[dict]:
    """Собирает историю: system, примеры (user -> assistant), затем реальное падение.

    Примеры подаются как прошлый «диалог»: модель видит, как она якобы уже отвечала.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for example_text, example_answer in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example_text})
        answer_json = json.dumps(example_answer, ensure_ascii=False)
        messages.append({"role": "assistant", "content": answer_json})
    messages.append({"role": "user", "content": failure_text})
    return messages


def classify_failure(failure_text: str, client: OllamaClient) -> FailureClassification:
    """Отправляет падение модели и возвращает проверенный результат.

    Если ответ не прошёл проверку Pydantic — переспрашивает (до MAX_ATTEMPTS раз).
    """
    messages = build_messages(failure_text)
    schema = FailureClassification.model_json_schema()

    last_error = None
    for _ in range(MAX_ATTEMPTS):
        result = client.chat(messages, response_format=schema)
        try:
            return FailureClassification.model_validate_json(result.content)
        except ValidationError as e:
            last_error = e

    raise ClassificationError(f"Модель не вернула валидный JSON: {last_error}")


def evidence_found(classification: FailureClassification, failure_text: str) -> bool:
    """Проверка на галлюцинацию: цитата должна дословно встречаться в тексте падения."""
    quote = classification.evidence.strip()
    return quote != "" and quote in failure_text
