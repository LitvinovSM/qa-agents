from dataclasses import dataclass, field

from qa_agents.dto.ollama.tool_call import ToolCall

NANOSECONDS_IN_SECOND = 1_000_000_000


@dataclass
class ChatResult:
    """Ответ модели (POST /api/chat): текст или просьбы вызвать инструменты + токены + время.

    Токены и время — наша «стоимость» запроса при работе с локальной моделью.
    """

    content: str
    input_tokens: int
    output_tokens: int
    seconds: float
    tool_calls: list[ToolCall] = field(default_factory=list)

    @staticmethod
    def from_api(data: dict) -> "ChatResult":
        """Собирает DTO из JSON ответа /api/chat. Время в ответе — в наносекундах."""
        message = data.get("message", {})
        tool_calls: list[ToolCall] = []
        for item in message.get("tool_calls") or []:
            tool_calls.append(ToolCall.from_api(item))
        return ChatResult(
            content=message.get("content", ""),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            seconds=data.get("total_duration", 0) / NANOSECONDS_IN_SECOND,
            tool_calls=tool_calls,
        )

    def as_assistant_message(self) -> dict:
        """Ответ модели в виде сообщения для истории (роль assistant, с её tool_calls)."""
        message = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            message["tool_calls"] = [call.to_api() for call in self.tool_calls]
        return message
