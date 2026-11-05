import json
import sys
from pathlib import Path

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.dto.ollama.chat_result import ChatResult
from qa_agents.errors import OllamaUnavailableError, ClassificationError
from qa_agents.services.classifier_batch import classify_failure_list

PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "sample_failures.json"


def main() -> int:
    """Классифицирует все падения одним списком и печатает итог «совпало X из N»."""
    failures = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    client = OllamaClient()

    failureList =[]
    for failure in failures:
        failure_id_plus_text = f"{failure["id"]}: {failure["failure_text"]}"
        failureList.append(failure_id_plus_text)
    try:
        result: ChatResult = classify_failure_list(failureList, client)
    except OllamaUnavailableError as e:
        print("[ОШИБКА]", e)
        return 1
    except ClassificationError as e:
        print("[НЕ РАЗОБРАНО]", e)
        return 1
    print("Разбор закончен")
    print("Модель разобрала список падений и ответила следующим результатом ")
    print(f"{client.chat_result_as_json(result)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())