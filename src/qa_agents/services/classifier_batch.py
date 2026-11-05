import json

from pydantic import ValidationError

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.dto.classificator.batchFailureClassificator.batch_classification import BatchClassification
from qa_agents.dto.ollama.chat_result import ChatResult
from qa_agents.errors import ClassificationError
from qa_agents.prompts.classifier_prompt import FEW_SHOT_EXAMPLES, SYSTEM_PROMPT


SCHEMA = BatchClassification.model_json_schema()
SCHEMA_TEXT = json.dumps(SCHEMA, ensure_ascii=False)
MAX_ATTEMPTS = 2


def build_messages(failure_text: str) -> list[dict]:
    system_content = (
        f"{SYSTEM_PROMPT}\n\nСхема ответа (JSON Schema). Учитывай описания полей:\n{SCHEMA_TEXT}"
    )

    messages = [{"role": "system", "content": system_content}]
    for example_text, example_answer in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example_text})
        answer_json = json.dumps(example_answer, ensure_ascii=False)
        messages.append({"role": "assistant", "content": answer_json})
    messages.append({"role": "user", "content": failure_text})
    return messages



def classify_failure_list(failure_list: list[str], client: OllamaClient) -> ChatResult:
    """Отправляет падение модели и возвращает проверенный результат.

    Если ответ не прошёл проверку Pydantic — переспрашивает (до MAX_ATTEMPTS раз).
    """
    messages = build_messages("\n".join(failure_list))
    schema = BatchClassification.model_json_schema()

    last_error = None
    for _ in range(MAX_ATTEMPTS):
        result = client.chat(messages, response_format=schema)
        print(f"От модели получили ответ вида: {json.dumps(json.loads(result.content), indent=4, ensure_ascii=False)}")
        try:
            BatchClassification.model_validate_json(result.content)
            return result
        except ValidationError as e:
            last_error = e

    raise ClassificationError(f"Модель не вернула валидный JSON: {last_error}")


def get_result_content_as_BatchClassification(result: ChatResult) -> BatchClassification:
    return BatchClassification.model_validate_json(result.content)

