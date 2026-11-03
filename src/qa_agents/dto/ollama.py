"""DTO ответов API Ollama: скачанная модель, модель в памяти, ответ модели."""

from dataclasses import dataclass

BYTES_IN_GB = 1024**3
NANOSECONDS_IN_SECOND = 1_000_000_000


@dataclass
class ModelInfo:
    """Скачанная модель — одна строка из `ollama list` (GET /api/tags)."""

    name: str
    size_bytes: int
    parameter_size: str
    quantization: str

    @property
    def size_gb(self) -> float:
        """Размер в гигабайтах (Ollama отдаёт в байтах)."""
        return self.size_bytes / BYTES_IN_GB

    @staticmethod
    def from_api(data: dict) -> "ModelInfo":
        """Собирает DTO из JSON ответа (ручной аналог Jackson).

        .get() с умолчанием — чтобы не упасть, если поле пропало из ответа.
        """
        details = data.get("details", {})
        return ModelInfo(
            name=data.get("name", "unknown"),
            size_bytes=data.get("size", 0),
            parameter_size=details.get("parameter_size", "?"),
            quantization=details.get("quantization_level", "?"),
        )


@dataclass
class RunningModel:
    """Модель в памяти — одна строка из `ollama ps` (GET /api/ps)."""

    name: str
    size_bytes: int
    size_vram_bytes: int
    context_length: int

    @property
    def size_gb(self) -> float:
        """Сколько памяти занимает модель всего (VRAM + RAM), в гигабайтах."""
        return self.size_bytes / BYTES_IN_GB

    @property
    def gpu_percent(self) -> float:
        """Какая доля модели лежит в видеопамяти — колонка PROCESSOR из `ollama ps`."""
        if self.size_bytes == 0:
            return 0.0
        return self.size_vram_bytes / self.size_bytes * 100

    @staticmethod
    def from_api(data: dict) -> "RunningModel":
        """Собирает DTO из JSON ответа /api/ps."""
        return RunningModel(
            name=data.get("name", "unknown"),
            size_bytes=data.get("size", 0),
            size_vram_bytes=data.get("size_vram", 0),
            context_length=data.get("context_length", 0),
        )


@dataclass
class ChatResult:
    """Ответ модели (POST /api/chat): текст + токены входа/выхода + время.

    Токены и время — наша «стоимость» запроса при работе с локальной моделью.
    """

    content: str
    input_tokens: int
    output_tokens: int
    seconds: float

    @staticmethod
    def from_api(data: dict) -> "ChatResult":
        """Собирает DTO из JSON ответа /api/chat. Время в ответе — в наносекундах."""
        message = data.get("message", {})
        return ChatResult(
            content=message.get("content", ""),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            seconds=data.get("total_duration", 0) / NANOSECONDS_IN_SECOND,
        )
