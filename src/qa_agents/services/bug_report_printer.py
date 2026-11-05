from qa_agents.dto.bugReport.bug_report import BugReport
from qa_agents.services.bug_report_extractor import evidence_found


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
