"""Тесты классификатора без Ollama: модель подменяем заглушкой с заготовленными ответами."""

import pytest
from pydantic import ValidationError

from qa_agents.dto.classification import FailureClassification
from qa_agents.dto.ollama import ChatResult
from qa_agents.errors import ClassificationError
from qa_agents.services.classifier import classify_failure, evidence_found

VALID_JSON = (
    '{"reasoning": "Сервис недоступен", "evidence": "Connection refused", '
    '"category": "environment", "confidence": 0.9}'
)


class FakeClient:
    """Заглушка вместо OllamaClient: по очереди отдаёт заготовленные ответы, считает вызовы."""

    def __init__(self, answers: list[str]) -> None:
        self.answers = answers
        self.calls = 0

    def chat(self, messages, response_format=None) -> ChatResult:
        answer = self.answers[self.calls]
        self.calls = self.calls + 1
        return ChatResult(content=answer, input_tokens=0, output_tokens=0, seconds=0.0)


def test_valid_json_is_parsed():
    result = FailureClassification.model_validate_json(VALID_JSON)

    assert result.category == "environment"
    assert result.confidence == 0.9


def test_unknown_category_is_rejected():
    # Модель выдумала класс, которого нет в списке, — Pydantic не пропускает.
    bad = VALID_JSON.replace("environment", "network_problem")

    with pytest.raises(ValidationError):
        FailureClassification.model_validate_json(bad)


def test_confidence_above_one_is_rejected():
    bad = VALID_JSON.replace("0.9", "1.5")

    with pytest.raises(ValidationError):
        FailureClassification.model_validate_json(bad)


def test_retry_after_broken_json():
    # Первая попытка — мусор, вторая — валидный JSON: должны получить результат со 2-го раза.
    client = FakeClient(["это не JSON", VALID_JSON])

    result = classify_failure("Connection refused", client)

    assert result.category == "environment"
    assert client.calls == 2


def test_error_when_all_attempts_broken():
    client = FakeClient(["мусор", "снова мусор"])

    with pytest.raises(ClassificationError):
        classify_failure("Connection refused", client)


def test_evidence_found_and_hallucinated():
    result = FailureClassification.model_validate_json(VALID_JSON)

    assert evidence_found(result, "java.net.ConnectException: Connection refused") is True
    assert evidence_found(result, "NullPointerException at Foo") is False
