import sys

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.dto.bugReport.bug_report import BugReport
from qa_agents.errors import ClassificationError, OllamaUnavailableError
from qa_agents.services.bug_report_extractor import build_report, evidence_found



def print_report(report: BugReport, description: str) -> None:
    """Печатает баг-репорт в консоль в читаемом виде."""
    print(f"Заголовок: {report.title}")

    print("Шаги к воспроизведению:")
    for number, step in report.steps:
        print(f"  {number}. {step}")

    print(f"Ожидаемый результат: {report.expected or 'не указан'}")
    print(f"Фактический результат: {report.actual}")
    print(f"Логи: {report.logs or 'отсутствуют'}")

    env = report.environment
    print("Окружение:")
    print(f"  Где обнаружен: {env.side or 'не определено'}")
    print(f"  Версия: {env.app_version or 'не указана'}")
    print(f"  Стенд: {env.stand}")

    print(f"Приоритет: {report.priority}")
    print(f"Цитата-обоснование: {report.evidence}")
    print(f"Уверенность модели: {report.confidence:.0%}")
    print(f"Цитата найдена в описании: {evidence_found(report, description)}")
    print("-" * 60)




def main() -> int:
    """Читает описания багов из консоли и печатает по каждому баг-репорт."""
    client = OllamaClient()
    print("Опиши баг как в чате, и я составлю баг-репорт. Выход: /bye")

    while True:
        description = input("Баг: ").strip()

        if description == "/bye":
            break
        if not description:
            continue

        try:
            report = build_report(description, client)
        except OllamaUnavailableError as e:
            print("[ОШИБКА]", e)
            return 1
        except ClassificationError as e:
            print("[НЕ РАЗОБРАНО]", e)
            continue

        print()
        print_report(report, description)

    print("Работа завершена")
    return 0


if __name__ == "__main__":
    sys.exit(main())
