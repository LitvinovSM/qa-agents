"""ЗАДАНИЕ 2: оценка, поместится ли модель в видеопамять.

Замени строки `raise NotImplementedError(...)` на расчёт.
Готово, когда `uv run pytest` показывает 9 passed.
"""

BITS_IN_BYTE = 8


def estimate_gb(params_billion: float, bits: float = 4.5) -> float:
    """Примерный размер весов модели в ГБ.

    Формула: параметры_в_млрд × бит_на_параметр / 8. Пример: 4 × 4.5 / 8 = 2.25.
    """
    # TODO: return <формула>
    raise NotImplementedError("Задание 2: напиши формулу в estimate_gb")


def fits(model_gb: float, vram_gb: float = 4.0, overhead_gb: float = 0.8) -> bool:
    """Поместится ли модель целиком в видеопамять.

    Условие: размер_модели + запас (KV-кеш, буферы) <= объём_видеопамяти.
    """
    # TODO: return <условие>
    raise NotImplementedError("Задание 2: напиши условие в fits")
