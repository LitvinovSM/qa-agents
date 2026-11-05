import json

from pydantic import ValidationError

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.dto.bugReport.bug_report import BugReport
from qa_agents.errors import ClassificationError
from qa_agents.prompts.bug_report_promt import FEW_SHOT_EXAMPLES, SYSTEM_PROMPT

# Сколько раз переспрашивать модель, если она вернула невалидный JSON.
MAX_ATTEMPTS = 2
# Схема ответа как словарь: её получает Ollama для жёстких ограничений структуры.
SCHEMA = BugReport.model_json_schema()

# Та же схема, но текстом: её мы положим в промт, чтобы модель прочитала описания полей.
SCHEMA_TEXT = json.dumps(SCHEMA, ensure_ascii=False)

def build_messages(potential_problem_text: str) -> list[dict]:
    """Собираем сообщение для отправки и составления описания бага из:
    1) Роли
    2) Примеров проблем
    3) Текущей проблемы
    """
    system_content = (
        f"{SYSTEM_PROMPT}\n\nСхема ответа (JSON Schema). Учитывай описания полей:\n{SCHEMA_TEXT}"
    )
    messages = [{"role": "system", "content": system_content}]
    for example_text, example_answer in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example_text})
        answer_json = json.dumps(example_answer, ensure_ascii=False)
        messages.append({"role": "assistant", "content": answer_json})
    messages.append({"role": "user", "content": potential_problem_text})
    return messages

def build_report(potential_problem_text: str, client: OllamaClient) -> BugReport:
    messages = build_messages(potential_problem_text)
    schema = BugReport.model_json_schema()

    last_error = None
    for _ in range(MAX_ATTEMPTS):
        result = client.chat(messages, response_format=schema)
        print(
            f"От модели получили ответ вида: {json.dumps(json.loads(result.content), indent=4, ensure_ascii=False)}"
        )
        try:
            return BugReport.model_validate_json(result.content)
        except ValidationError as e:
            last_error = e

    raise ClassificationError(f"Модель не вернула валидный JSON: {last_error}")


def evidence_found(classification: BugReport, potential_problem: str) -> bool:
    """Проверка на галлюцинацию: цитата должна дословно встречаться в тексте падения."""
    quote = classification.evidence.strip()
    return quote != "" and quote in potential_problem