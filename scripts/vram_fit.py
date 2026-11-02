"""Задание 2 (часть 2): сравнить расчёт по формуле с реальными размерами моделей.

Запускай ПОСЛЕ того, как допишешь функции в src/qa_agents/vram.py
и тесты станут зелёными:
    uv run python scripts/vram_fit.py
"""

import sys

from qa_agents.config import GPU_VRAM_GB
from qa_agents.ollama_client import OllamaClient, OllamaUnavailableError
from qa_agents.vram import estimate_gb, fits

# Сколько миллиардов параметров у моделей, которые мы сравниваем.
# Это СЛОВАРЬ (dict): ключ — имя модели, значение — число параметров.
# Аналог Java: Map<String, Double> = Map.of("qwen3.5:2b", 2.0, ...).
# Фигурные скобки {} с парами "ключ": значение — так создаётся словарь.
MODEL_PARAMS_BILLION: dict[str, float] = {
    "qwen3.5:2b": 2.0,
    "qwen3.5:4b": 4.0,
    "qwen3.5:9b": 9.0,
}


def main() -> int:
    # Сначала пробуем узнать реальные размеры из Ollama.
    # Если Ollama не запущена — не страшно, просто покажем только расчёт.
    real_sizes: dict[str, float] = {}  # пустой словарь
    try:
        for model in OllamaClient().list_models():
            # словарь[ключ] = значение — положить пару в словарь (аналог map.put).
            real_sizes[model.name] = model.size_gb
    except OllamaUnavailableError:
        print("[!] Ollama недоступна — реальные размеры показать не получится.\n")

    print(f"Видеопамять: {GPU_VRAM_GB} ГБ\n")
    print(f"{'Модель':<15}{'Расчёт':>10}{'Реально':>10}  Влезет по расчёту?")

    # .items() — перебрать пары (ключ, значение). Аналог map.entrySet().
    # `for name, params in ...` — сразу «распаковываем» пару в две переменные.
    for name, params in MODEL_PARAMS_BILLION.items():
        estimated = estimate_gb(params)

        # Если модель скачана — берём реальный размер, иначе пишем "-".
        # `x if условие else y` — аналог тернарного оператора Java: условие ? x : y.
        if name in real_sizes:
            real_text = f"{real_sizes[name]:.1f} ГБ"
        else:
            real_text = "-"

        verdict = "да" if fits(estimated, vram_gb=GPU_VRAM_GB) else "нет"
        print(f"{name:<15}{estimated:>7.2f} ГБ{real_text:>10}  {verdict}")

    # TODO (часть задания): ниже одной строкой комментария объясни,
    # почему реальный размер qwen3.5 больше расчётного.
    # Ответ: ...

    return 0


if __name__ == "__main__":
    sys.exit(main())
