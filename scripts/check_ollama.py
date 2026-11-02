"""Задание 1: проверка, что Ollama жива, и что в ней есть.

Запуск (из корня проекта, в PowerShell):
    uv run python scripts/check_ollama.py

Что делает:
    1. Печатает версию Ollama.
    2. Печатает список скачанных моделей с размером — как `ollama list`.
    3. Печатает модели, загруженные в память, и сколько % лежит на GPU —
       как `ollama ps`.
    Если Ollama не запущена — печатает понятное сообщение вместо стектрейса.
"""

# sys — стандартный модуль; нам из него нужен sys.exit() (аналог System.exit()).
import sys

# Подключаем наш клиент и наше исключение из пакета qa_agents.
from qa_agents.ollama_client import OllamaClient, OllamaUnavailableError


# Функция main — «точка входа» скрипта. Имя main — договорённость, не правило.
def main() -> int:
    # Создаём клиента. Аналог Java: OllamaClient client = new OllamaClient();
    # Аргументы не передаём — возьмутся значения по умолчанию из config.py.
    client = OllamaClient()

    try:
        version = client.get_version()
        models = client.list_models()
        running = client.list_running_models()
    except OllamaUnavailableError as e:
        # print(...) — вывести в консоль. Аналог System.out.println(...).
        print(f"[ОШИБКА] {e}")
        # Код возврата 1 = «что-то пошло не так». Пригодится в CI (День 7):
        # Jenkins считает шаг упавшим, если программа вернула не 0.
        return 1

    print(f"Ollama работает, версия: {version}")
    print()  # пустая строка для читаемости

    # --- Скачанные модели ----------------------------------------------------
    # len(список) — длина списка. Аналог list.size().
    print(f"Скачано моделей: {len(models)}")

    # `if not models:` — «если список пустой». Пустой список в Python
    # считается «ложью», поэтому так проверяют пустоту (вместо list.isEmpty()).
    if not models:
        print("  Моделей нет. Скачай: ollama pull qwen3.5:4b")

    for model in models:
        # f"{значение:.1f}" — формат «число с 1 знаком после запятой».
        # Аналог Java: String.format("%.1f", value).
        # f"{значение:<15}" — выровнять по левому краю в поле шириной 15 символов.
        # Аналог Java: String.format("%-15s", value).
        print(
            f"  {model.name:<15} {model.size_gb:>5.1f} ГБ  "
            f"параметров: {model.parameter_size:<6} квантизация: {model.quantization}"
        )

    print()

    # --- Модели в памяти -----------------------------------------------------
    print(f"Загружено в память сейчас: {len(running)}")
    if not running:
        print("  Ни одна модель не загружена (это нормально: Ollama выгружает их")
        print("  через ~5 минут простоя). Запусти `ollama run qwen3.5:4b` и повтори.")

    for item in running:
        # 100 - gpu_percent = сколько процентов модели работает на CPU.
        cpu_percent = 100 - item.gpu_percent
        print(
            f"  {item.name:<15} {item.size_gb:>5.1f} ГБ  "
            f"CPU/GPU: {cpu_percent:.0f}%/{item.gpu_percent:.0f}%  "
            f"контекст: {item.context_length}"
        )

    # Код возврата 0 = «всё хорошо».
    return 0


# Это условие истинно, только когда файл запускают напрямую
# (`python scripts/check_ollama.py`), а не импортируют из другого файла.
# Аналог Java: public static void main(String[] args) — точка запуска.
# sys.exit(main()) — вызвать main() и завершить программу с её кодом возврата.
if __name__ == "__main__":
    sys.exit(main())
