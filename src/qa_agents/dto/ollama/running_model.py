from dataclasses import dataclass

BYTES_IN_GB = 1024**3

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
