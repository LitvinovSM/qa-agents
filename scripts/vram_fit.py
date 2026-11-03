"""ЗАДАНИЕ 2 (часть 2): сравниваем расчёт по формуле с реальным размером модели.

Для каждой скачанной модели берём из Ollama три значения:
сколько параметров, как сильно сжата, сколько весит файл.
Считаем размер по формуле и сравниваем с реальным.

Запуск: uv run python scripts/vram_fit.py
"""

import sys

from qa_agents.config import GPU_VRAM_GB
from qa_agents.ollama_client import OllamaClient, OllamaUnavailableError
from qa_agents.vram import estimate_gb, fits

# Сколько бит в среднем занимает одно число при каждом виде сжатия (приблизительно).
BITS_BY_QUANTIZATION = {
    "Q4_K_M": 4.8,
    "Q8_0": 8.5,
    "F16": 16.0,
}

# 1 ГБ = 1 миллиард байт (так же, как в формуле estimate_gb).
BYTES_IN_GB = 1_000_000_000

# Запас памяти под текст, который модель читает и пишет.
OVERHEAD_GB = 0.8


def parse_params_billion(parameter_size: str) -> float:
    """Превращает строку из API "4.2B" в число 4.2 (B = billion, миллиард)."""
    number_text = parameter_size.replace("B", "")
    return float(number_text)


def main() -> int:
    """Для каждой модели печатает: расчёт по формуле, реальный размер, влезет ли в видеокарту."""
    try:
        models = OllamaClient().list_models()
    except OllamaUnavailableError as e:
        print("[ОШИБКА]", e)
        return 1

    print("Видеопамять:", GPU_VRAM_GB, "ГБ")
    print("Запас под текст:", OVERHEAD_GB, "ГБ")

    for model in models:
        # 1. Что знаем о модели из ответа API.
        params = parse_params_billion(model.parameter_size)
        bits = BITS_BY_QUANTIZATION.get(model.quantization)

        print()
        print("Модель:", model.name)
        print("  Параметров (млрд):", params)

        if bits is None:
            print("  Неизвестный вид сжатия", model.quantization, "- пропускаем")
            continue

        print("  Сжатие:", model.quantization, "=", bits, "бит на число")

        # 2. Расчёт по формуле (твоя функция из vram.py).
        estimated = round(estimate_gb(params, bits), 2)
        print("  Расчёт по формуле:", params, "x", bits, "/ 8 =", estimated, "ГБ")

        # 3. Реальный размер: поле "size" из ответа API, в байтах.
        real = round(model.size_bytes / BYTES_IN_GB, 2)
        print("  Реальный файл:", model.size_bytes, "байт =", real, "ГБ")

        # 4. Разница — всё, чего нет в формуле: «зрение» и служебные части модели.
        difference = round(real - estimated, 2)
        print("  Разница (зрение и служебные части):", difference, "ГБ")

        # 5. Влезет ли РЕАЛЬНЫЙ файл вместе с запасом (твоя функция из vram.py).
        total = round(real + OVERHEAD_GB, 2)
        if fits(real, GPU_VRAM_GB, OVERHEAD_GB):
            verdict = "да, целиком на видеокарте"
        else:
            verdict = "нет, часть уйдёт на процессор"
        print("  Нужно памяти:", real, "+", OVERHEAD_GB, "=", total, "ГБ ->", verdict)

    # Почему реальный размер больше расчётного (твой ответ):
    # нужна память на дополнительную обвязку, на «вижен» (хотя мы его не используем) и т.д.

    return 0


if __name__ == "__main__":
    sys.exit(main())