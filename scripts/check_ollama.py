"""ЗАДАНИЕ 1: проверка Ollama — версия, скачанные модели, модели в памяти.

Запуск: uv run python scripts/check_ollama.py
Если Ollama не запущена — понятное сообщение вместо стектрейса и код возврата 1.
"""

import sys

from qa_agents.ollama_client import OllamaClient, OllamaUnavailableError


def main() -> int:
    """Печатает состояние Ollama. Возвращает 0 — всё хорошо, 1 — Ollama недоступна.

    Код возврата важен для CI: Jenkins считает шаг упавшим при ненулевом коде.
    """
    client = OllamaClient()

    try:
        version = client.get_version()
        models = client.list_models()
        running = client.list_running_models()
    except OllamaUnavailableError as e:
        print(f"[ОШИБКА] {e}")
        return 1

    print(f"Ollama работает, версия: {version}")
    print()

    # Скачанные модели — как `ollama list`.
    print(f"Скачано моделей: {len(models)}")
    if not models:
        print("  Моделей нет. Скачай: ollama pull qwen3.5:4b")
    for model in models:
        print(
            f"  {model.name:<15} {model.size_gb:>5.1f} ГБ  "
            f"параметров: {model.parameter_size:<6} квантизация: {model.quantization}"
        )

    print()

    # Модели в памяти — как `ollama ps`.
    print(f"Загружено в память сейчас: {len(running)}")
    if not running:
        print("  Ни одна модель не загружена (Ollama выгружает их через ~5 минут простоя).")
        print("  Запусти `ollama run qwen3.5:4b` в другом окне и повтори.")
    for item in running:
        cpu_percent = 100 - item.gpu_percent
        print(
            f"  {item.name:<15} {item.size_gb:>5.1f} ГБ  "
            f"CPU/GPU: {cpu_percent:.0f}%/{item.gpu_percent:.0f}%  "
            f"контекст: {item.context_length}"
        )

    return 0


# Точка входа, аналог public static void main.
if __name__ == "__main__":
    sys.exit(main())
