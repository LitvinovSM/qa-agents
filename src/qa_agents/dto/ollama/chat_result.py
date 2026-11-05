from dataclasses import dataclass

NANOSECONDS_IN_SECOND = 1_000_000_000


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
