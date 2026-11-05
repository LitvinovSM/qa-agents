import sys

from qa_agents.clients.ollama_client import OllamaClient
from qa_agents.errors import ClassificationError, OllamaUnavailableError
from qa_agents.services.bug_report_extractor import build_report
from qa_agents.services.bug_report_printer import print_report


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
