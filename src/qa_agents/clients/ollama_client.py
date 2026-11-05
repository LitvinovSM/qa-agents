"""HTTP-клиент к API Ollama (аналог твоего клиента над RestAssured).

Только транспорт: отправить запрос, разобрать ответ в DTO, превратить сетевые ошибки в свои.
"""

import json
from dataclasses import asdict

import requests

from qa_agents.config import (
    CHAT_TIMEOUT_SECONDS,
    DEFAULT_MODEL,
    DEFAULT_NUM_CTX,
    OLLAMA_BASE_URL,
    REQUEST_TIMEOUT_SECONDS,
)
from qa_agents.dto.ollama.chat_result import ChatResult
from qa_agents.dto.ollama.model_info import ModelInfo
from qa_agents.dto.ollama.running_model import RunningModel
from qa_agents.errors import OllamaUnavailableError


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
        response_format: dict | None = None,
        tools: list[dict] | None = None,
    ) -> ChatResult:
        """Отправляет историю сообщений модели и возвращает её ответ (POST /api/chat).

        По умолчанию: temperature 0, режим размышлений выключен.
        response_format — JSON Schema: модель обязана ответить JSON-ом ровно такой формы.
        tools — описания инструментов: модель может попросить вызвать любой из них.
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
        if response_format is not None:
            payload["format"] = response_format
        if tools is not None:
            payload["tools"] = tools
        data = self._send("POST", "/api/chat", payload, CHAT_TIMEOUT_SECONDS)
        return ChatResult.from_api(data)

    def chat_result_as_json(self, chat_result: ChatResult) -> str:
        return f"{json.dumps(asdict(chat_result), indent=4, ensure_ascii=False)}"

    def chat_content_as_json(self, chat_result: ChatResult) -> str:
        try:
            return json.dumps(json.loads(chat_result.content), indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            return chat_result.content
