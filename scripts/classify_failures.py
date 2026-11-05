"""Модуль 1.3: классифицирует учебные падения из data/sample_failures.json.

Для каждого падения печатает решение модели и сравнивает с ожидаемым классом.
Запуск: uv run python scripts/classify_failures.py
"""

import json
import sys
from pathlib import Path

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.errors import ClassificationError, OllamaUnavailableError
from qa_agents.services.classifier import classify_failure, evidence_found

# Путь к данным считаем от этого файла, чтобы скрипт работал из любой папки (и из PyCharm).
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "sample_failures.json"


def main() -> int:
    """Классифицирует все падения по очереди и печатает итог «совпало X из N»."""
    failures = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    client = OllamaClient()
    correct = 0

    for failure in failures:
        print()
        print("=====", failure["id"], failure["test_name"], "=====")
        try:
            result = classify_failure(failure["failure_text"], client)
        except OllamaUnavailableError as e:
            print("[ОШИБКА]", e)
            return 1
        except ClassificationError as e:
            print("[НЕ РАЗОБРАНО]", e)
            continue

        is_correct = result.category == failure["expected"]
        if is_correct:
            correct = correct + 1

        print(
            "Ожидалось:", failure["expected"], "| Модель:", result.category, "| Верно:", is_correct
        )
        print("Уверенность:", result.confidence)
        print("Почему:", result.reasoning)
        print("Цитата:", result.evidence)
        print("Цитата есть в логе:", evidence_found(result, failure["failure_text"]))

    print()
    print("ИТОГО: верно", correct, "из", len(failures))
    return 0


if __name__ == "__main__":
    sys.exit(main())
