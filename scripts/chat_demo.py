"""Модуль 1.2: три опыта с моделью через наш клиент.

1. Роль system: как системная инструкция меняет ответ.
2. Память: модель «помнит» только то, что мы прислали в messages.
3. Temperature: насколько стабилен ответ при 0 и при 1.

Запуск: uv run python scripts/chat_demo.py
"""

import sys

from qa_agents.ollama_client import OllamaClient, OllamaUnavailableError

FAILURE = "Тест упал с java.net.ConnectException: Connection refused (localhost:8080)."


def demo_system_role(client: OllamaClient) -> None:
    """Один и тот же вопрос без system и с system — сравниваем ответы."""
    print("===== ОПЫТ 1: роль system =====")

    question = {"role": "user", "content": FAILURE + " Что это за проблема?"}

    without_system = client.chat([question])
    print("Без system:", without_system.content)
    print("  токенов на выходе:", without_system.output_tokens)

    system = {
        "role": "system",
        "content": "Ты классификатор падений автотестов. Отвечай ОДНИМ словом из списка: "
        "product_bug, flaky, environment, test_data.",
    }
    with_system = client.chat([system, question])
    print("С system:", with_system.content)
    print("  токенов на выходе:", with_system.output_tokens)


def demo_memory(client: OllamaClient) -> None:
    """Второй вопрос отсылает к первому. Без истории модель не понимает, о чём речь."""
    print()
    print("===== ОПЫТ 2: память = список сообщений =====")

    first_question = {"role": "user", "content": FAILURE + " Это проблема окружения?"}
    first_answer = client.chat([first_question])
    print("Вопрос 1 -> ответ:", first_answer.content)

    second_question = {"role": "user", "content": "А какой порт был в ошибке?"}

    # Без истории: отправляем только второй вопрос.
    no_history = client.chat([second_question])
    print("Вопрос 2 БЕЗ истории:", no_history.content)

    # С историей: прошлый вопрос + ответ модели (роль assistant) + новый вопрос.
    history = [
        first_question,
        {"role": "assistant", "content": first_answer.content},
        second_question,
    ]
    with_history = client.chat(history)
    print("Вопрос 2 С историей:", with_history.content)
    print("  токенов на входе без истории:", no_history.input_tokens)
    print("  токенов на входе с историей:", with_history.input_tokens)


def demo_temperature(client: OllamaClient) -> None:
    """Задаём один вопрос по 3 раза при temperature 0 и 1 — смотрим, меняется ли ответ."""
    print()
    print("===== ОПЫТ 3: temperature =====")

    question = {
        "role": "user",
        "content": "Придумай короткое название (3-5 слов) для баг-репорта: " + FAILURE,
    }

    for temperature in [0.0, 1.0]:
        print("temperature =", temperature)
        for attempt in range(1, 4):
            result = client.chat([question], temperature=temperature)
            print("  попытка", attempt, ":", result.content)


def main() -> int:
    """Запускает три опыта по очереди. Каждый вызов модели — несколько секунд."""
    client = OllamaClient()
    try:
        demo_system_role(client)
        demo_memory(client)
        demo_temperature(client)
    except OllamaUnavailableError as e:
        print("[ОШИБКА]", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
