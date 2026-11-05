
import json
import sys
from pathlib import Path

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.errors import ClassificationError, OllamaUnavailableError
from qa_agents.services.bug_report_extractor import build_report, evidence_found

# Путь к данным считаем от этого файла, чтобы скрипт работал из любой папки (и из PyCharm).
PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "bug_descriptions.json"


def main() -> int:
    """Классифицирует все падения по очереди и печатает итог «совпало X из N»."""
    problems_list = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    client = OllamaClient()

    for problem in problems_list:
        print()
        print("=====", problem["id"], "=====")
        try:
            result = build_report(problem["description"], client)
        except OllamaUnavailableError as e:
            print("[ОШИБКА]", e)
            return 1
        except ClassificationError as e:
            print("[НЕ РАЗОБРАНО]", e)
            continue

        print(f"Заголовок: {result.title}")

        print("Шаги к воспроизведению:")
        for number, step in result.steps:
            print(f"  {number}. {step}")

        print(f"Ожидаемый результат: {result.expected or 'не указан'}")
        print(f"Фактический результат: {result.actual}")
        print(f"Логи: {result.logs or 'отсутствуют'}")

        env = result.environment
        print("Окружение:")
        print(f"  Где обнаружен: {env.side or 'не определено'}")
        print(f"  Версия: {env.app_version or 'не указана'}")
        print(f"  Стенд: {env.stand}")

        print(f"Приоритет: {result.priority}")
        print(f"Цитата-обоснование: {result.evidence}")
        print(f"Уверенность модели: {result.confidence:.0%}")
        print(f"Цитата найдена в описании: {evidence_found(result, problem['description'])}")
        print("-" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())