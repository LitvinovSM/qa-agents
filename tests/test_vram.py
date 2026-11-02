"""Тесты к заданию 2 (функции из src/qa_agents/vram.py).

Запуск: uv run pytest

Пока функции не написаны — тесты красные (NotImplementedError).
Это нормально и ожидаемо: допиши функции, и тесты позеленеют.

Как pytest находит тесты (отличие от JUnit):
    - файл должен называться test_*.py;
    - функция должна называться test_*;
    - аннотация @Test НЕ нужна, проверка — обычный `assert`.
"""

# pytest — библиотека тестов. Из неё нам нужен approx (см. ниже).
import pytest

from qa_agents.vram import estimate_gb, fits


def test_estimate_4b_model():
    # 4 млрд × 4.5 бит / 8 = 2.25 ГБ.
    # pytest.approx — сравнение дробных чисел с допуском (числа с плавающей
    # точкой нельзя сравнивать через == точно).
    # Аналог JUnit: assertEquals(2.25, actual, 0.001).
    assert estimate_gb(4) == pytest.approx(2.25)


def test_estimate_with_8_bits():
    # 8 бит на параметр = 1 байт, значит 4 млрд параметров = 4 ГБ.
    assert estimate_gb(4, bits=8) == pytest.approx(4.0)


def test_small_model_fits():
    # 2.0 + 0.8 = 2.8 <= 4.0 → помещается.
    assert fits(2.0) is True


def test_qwen_4b_real_size_does_not_fit():
    # Реальный файл qwen3.5:4b ≈ 3.4 ГБ: 3.4 + 0.8 = 4.2 > 4.0 → не помещается.
    # Именно это ты и увидел в `ollama ps`: часть модели ушла на CPU.
    assert fits(3.4) is False


def test_boundary_exactly_full():
    # Граничное значение (ты как QA это оценишь): 3.2 + 0.8 = 4.0 — ровно впритык.
    # Считаем, что впритык — помещается (условие <=).
    assert fits(3.2) is True
