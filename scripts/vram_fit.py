"""ЗАДАНИЕ 2 (часть 2): сравнение расчёта по формуле с реальными размерами моделей.

Запуск после того, как vram.py дописан и тесты зелёные:
    uv run python scripts/vram_fit.py
"""

import sys

from qa_agents.config import GPU_VRAM_GB
from qa_agents.ollama_client import OllamaClient, OllamaUnavailableError
from qa_agents.vram import estimate_gb, fits

# Число параметров (в миллиардах) у моделей для сравнения.
MODEL_PARAMS_BILLION: dict[str, float] = {
    "qwen3.5:2b": 2.0,
    "qwen3.5:4b": 4.0,
    "qwen3.5:9b": 9.0,
}


def main() -> int:
    """Печатает таблицу: расчётный размер, реальный размер из Ollama, влезет ли в VRAM.

    Если Ollama не запущена — показывает только расчёт.
    """
    real_sizes: dict[str, float] = {}
    try:
        for model in OllamaClient().list_models():
            real_sizes[model.name] = model.size_gb
    except OllamaUnavailableError:
        print("[!] Ollama недоступна — реальные размеры показать не получится.\n")

    print(f"Видеопамять: {GPU_VRAM_GB} ГБ\n")
    print(f"{'Модель':<15}{'Расчёт':>10}{'Реально':>10}  Влезет по расчёту?")

    for name, params in MODEL_PARAMS_BILLION.items():
        estimated = estimate_gb(params)
        real_text = f"{real_sizes[name]:.1f} ГБ" if name in real_sizes else "-"
        verdict = "да" if fits(estimated, vram_gb=GPU_VRAM_GB) else "нет"
        print(f"{name:<15}{estimated:>7.2f} ГБ{real_text:>10}  {verdict}")

    # TODO: одной строкой объясни, почему реальный размер qwen3.5 больше расчётного.
    # Ответ: ...

    return 0


if __name__ == "__main__":
    sys.exit(main())
