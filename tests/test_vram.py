"""Тесты к заданию 2 (vram.py). Красные, пока функции не дописаны — это нормально."""

import pytest

from qa_agents.vram import estimate_gb, fits


def test_estimate_4b_model():
    # 4 × 4.5 / 8 = 2.25 ГБ. approx — сравнение дробей с допуском.
    assert estimate_gb(4) == pytest.approx(2.25)


def test_estimate_with_8_bits():
    # 8 бит = 1 байт на параметр → 4 ГБ.
    assert estimate_gb(4, bits=8) == pytest.approx(4.0)


def test_small_model_fits():
    # 2.0 + 0.8 = 2.8 <= 4.0
    assert fits(2.0) is True


def test_qwen_4b_real_size_does_not_fit():
    # 3.4 + 0.8 = 4.2 > 4.0 — то самое деление CPU/GPU из `ollama ps`.
    assert fits(3.4) is False


def test_boundary_exactly_full():
    # Граничное значение: 3.2 + 0.8 = 4.0 — впритык считается «помещается».
    assert fits(3.2) is True
