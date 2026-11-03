"""Исключения проекта в одном месте (аналог пакета exceptions в Java)."""


class OllamaUnavailableError(Exception):
    """Ollama не отвечает (не запущена, неверный адрес, таймаут).

    Одна понятная ошибка вместо десятка исключений requests.
    """


class ClassificationError(Exception):
    """Модель не вернула валидный JSON ни с одной попытки."""
