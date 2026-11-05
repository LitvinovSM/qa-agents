import json
import sys
from pathlib import Path

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.dto.classificator.batchFailureClassificator.batch_classification import BatchClassification
from qa_agents.dto.ollama.chat_result import ChatResult
from qa_agents.errors import OllamaUnavailableError, ClassificationError
from qa_agents.services.classifier_batch import (
    classify_failure_list,
    get_result_content_as_BatchClassification,
)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "sample_failures.json"


def main() -> int:
    """Классифицирует все падения одним списком и печатает итог «совпало X из N»."""
    failures = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    client = OllamaClient()

    failure_list =[]
    failure_id_set = set()
    for failure in failures:
        failure_id_plus_text = f"{failure["id"]}: {failure["failure_text"]}"
        failure_id_set.add(failure["id"])
        failure_list.append(failure_id_plus_text)
    try:
        result: ChatResult = classify_failure_list(failure_list, client)
    except OllamaUnavailableError as e:
        print("[ОШИБКА]", e)
        return 1
    except ClassificationError as e:
        print("[НЕ РАЗОБРАНО]", e)
        return 1
    batch_classification: BatchClassification = get_result_content_as_BatchClassification(result)
    print("Разбор закончен")
    print(f"Время обработки запроса: {result.seconds}")
    print(f"Входящие токены: {result.input_tokens}")
    fact_id_set=set()
    for item in batch_classification.items:
        fact_id_set.add(item.id)
        print("-------------------------")
        print(f"Классификация ошибки: {item.id}")
        print(f"Категория {item.category}")
        print(f"Обоснование {item.reasoning}")
    dif_id = failure_id_set-fact_id_set
    if dif_id:
        print(f"Было выявлено несоответствие идентификаторов (нужна перепроверка): {dif_id}")
    if not failure_id_set == fact_id_set:
        print(f"Было выявлено несоответствие идентификаторов (модель выдумала свои идентификаторы): {dif_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())