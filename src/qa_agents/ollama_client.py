"""HTTP-клиент к API Ollama.

Обёртка, как твой клиент над RestAssured во фреймворке автотестов:
скрипты зовут client.chat(...), а не пишут HTTP-запросы сами.
"""

from dataclasses import dataclass

import requests

from qa_agents.config import (
    CHAT_TIMEOUT_SECONDS,
    DEFAULT_MODEL,
    DEFAULT_NUM_CTX,
    OLLAMA_BASE_URL,
    REQUEST_TIMEOUT_SECONDS,
)

BYTES_IN_GB = 1024**3
NANOSECONDS_IN_SECOND = 1_000_000_000


class OllamaUnavailableError(Exception):
    """Ollama не отвечает (не запущена, неверный адрес, таймаут).

    Одна понятная ошибка вместо десятка исключений requests.
    """


@dataclass
class ModelInfo:
    """DTO скачанной модели — одна строка из `ollama list`."""

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
        """Собирает DTO из JSON ответа /api/tags (ручной аналог Jackson).

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
    """DTO модели в памяти — одна строка из `ollama ps`."""

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
    """DTO ответа модели: текст + сколько токенов прочитано/написано + сколько секунд.

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


class OllamaClient:
    """Клиент к Ollama: служебные запросы + запрос к самой модели (chat)."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        """Без аргументов берёт адрес и таймаут из config.py."""
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _send(self, method: str, path: str, payload: dict | None, timeout: int) -> dict:
        """Отправляет HTTP-запрос и возвращает JSON. Ошибки сети -> OllamaUnavailableError.

        Общий код для GET и POST, чтобы не дублировать обработку ошибок.
        """
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(method, url, json=payload, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise OllamaUnavailableError(
                f"Ollama не отвечает по адресу {self.base_url}. "
                "Проверь, что Ollama запущена (иконка ламы в трее) "
                "и что в браузере открывается http://localhost:11434"
            ) from e
        except requests.exceptions.Timeout as e:
            raise OllamaUnavailableError(
                f"Ollama не ответила за {timeout} с по адресу {url}"
            ) from e
        return response.json()

    def _get(self, path: str) -> dict:
        """GET-запрос к служебному API (короткий таймаут)."""
        return self._send("GET", path, None, self.timeout_seconds)

    def get_version(self) -> str:
        """Версия сервера Ollama (GET /api/version)."""
        data = self._get("/api/version")
        return data.get("version", "unknown")

    def list_models(self) -> list[ModelInfo]:
        """Скачанные модели, как `ollama list` (GET /api/tags)."""
        data = self._get("/api/tags")
        result: list[ModelInfo] = []
        for item in data.get("models", []):
            result.append(ModelInfo.from_api(item))
        return result

    def list_running_models(self) -> list[RunningModel]:
        """Модели, загруженные в память, как `ollama ps` (GET /api/ps)."""
        data = self._get("/api/ps")
        result: list[RunningModel] = []
        for item in data.get("models", []):
            result.append(RunningModel.from_api(item))
        return result

    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.0,
        num_ctx: int = DEFAULT_NUM_CTX,
    ) -> ChatResult:
        """Отправляет историю сообщений модели и возвращает её ответ (POST /api/chat).

        По умолчанию: temperature 0 (предсказуемо), режим размышлений выключен (быстро).
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
            },
        }
        data = self._send("POST", "/api/chat", payload, CHAT_TIMEOUT_SECONDS)
        return ChatResult.from_api(data)
