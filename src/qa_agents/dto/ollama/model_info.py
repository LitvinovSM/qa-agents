from dataclasses import dataclass

BYTES_IN_GB = 1024**3

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
