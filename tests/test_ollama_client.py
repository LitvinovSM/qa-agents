"""Тесты разбора JSON в DTO. В Ollama не ходят, поэтому проходят без неё."""

from qa_agents.ollama_client import ChatResult, ModelInfo, RunningModel


def test_model_info_from_api():
    data = {
        "name": "qwen3.5:4b",
        "size": 3 * 1024**3,
        "details": {"parameter_size": "4.7B", "quantization_level": "Q4_K_M"},
    }

    model = ModelInfo.from_api(data)

    assert model.name == "qwen3.5:4b"
    assert model.size_gb == 3.0
    assert model.quantization == "Q4_K_M"


def test_model_info_without_details():
    # Поле details пропало из ответа — не падаем, подставляем "?".
    model = ModelInfo.from_api({"name": "x", "size": 0})

    assert model.parameter_size == "?"


def test_running_model_gpu_percent():
    data = {"name": "qwen3.5:4b", "size": 3_000, "size_vram": 1_500}

    running = RunningModel.from_api(data)

    assert running.gpu_percent == 50.0


def test_running_model_zero_size_no_crash():
    # Граничный случай: нулевой размер не должен давать деление на ноль.
    running = RunningModel.from_api({"name": "x"})

    assert running.gpu_percent == 0.0


def test_chat_result_from_api():
    # Урезанный ответ /api/chat. Время в Ollama — в наносекундах.
    data = {
        "message": {"role": "assistant", "content": "Проблема окружения."},
        "prompt_eval_count": 68,
        "eval_count": 5,
        "total_duration": 2_500_000_000,
    }

    result = ChatResult.from_api(data)

    assert result.content == "Проблема окружения."
    assert result.input_tokens == 68
    assert result.output_tokens == 5
    assert result.seconds == 2.5
