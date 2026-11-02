"""Тесты для DTO из ollama_client.py.

Эти тесты НЕ ходят в Ollama — проверяют только разбор JSON в наши объекты.
Поэтому они проходят даже без запущенной Ollama.
Аналогия: юнит-тест десериализации DTO через Jackson на готовой JSON-строке.
"""

from qa_agents.ollama_client import ModelInfo, RunningModel


def test_model_info_from_api():
    # Кусок ответа /api/tags для одной модели (как вернул бы .json()).
    data = {
        "name": "qwen3.5:4b",
        "size": 3 * 1024**3,  # ровно 3 ГБ в байтах
        "details": {"parameter_size": "4.7B", "quantization_level": "Q4_K_M"},
    }

    model = ModelInfo.from_api(data)

    assert model.name == "qwen3.5:4b"
    assert model.size_gb == 3.0
    assert model.quantization == "Q4_K_M"


def test_model_info_without_details():
    # Защита от изменений API: если поля details нет — не падаем,
    # а подставляем "?".
    model = ModelInfo.from_api({"name": "x", "size": 0})

    assert model.parameter_size == "?"


def test_running_model_gpu_percent():
    # 3 ГБ всего, из них 1.5 ГБ на GPU → 50% на GPU.
    data = {"name": "qwen3.5:4b", "size": 3_000, "size_vram": 1_500}

    running = RunningModel.from_api(data)

    assert running.gpu_percent == 50.0


def test_running_model_zero_size_no_crash():
    # Граничный случай: размер 0 не должен приводить к делению на ноль.
    running = RunningModel.from_api({"name": "x"})

    assert running.gpu_percent == 0.0
