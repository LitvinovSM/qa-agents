"""Оценка, поместится ли модель в видеопамять (твоё решение задания 2)."""

BITS_IN_BYTE = 8


def estimate_gb(params_billion: float, bits: float = 4.5) -> float:
    """Примерный размер весов модели в ГБ.

    Формула: параметры_в_млрд × бит_на_параметр / 8. Пример: 4 × 4.5 / 8 = 2.25.
    """
    return params_billion * bits / BITS_IN_BYTE


def fits(model_gb: float, vram_gb: float = 4.0, overhead_gb: float = 0.8) -> bool:
    """Поместится ли модель целиком в видеопамять.

    Условие: размер_модели + запас (KV-кеш, буферы) <= объём_видеопамяти.
    """
    return model_gb + overhead_gb <= vram_gb
