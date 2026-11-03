from typing import Literal

from pydantic import BaseModel, Field
from dataclasses import dataclass

Priority = Literal["blocker", "critical", "high", "low"]
Stand = Literal["dev", "st", "ift", "preprod", "prod"]

@dataclass
class BugReport(BaseModel):
    """Класс под баг репорт для ответа Ollama"""
    title: str = Field(min_length=10, max_length=80, description="1 предложение: должно отвечать последовательно на вопросы Что?Где?Когда? обнаружен баг")
    steps: list[tuple[int,str]] = Field(min_length=1, description="Список нумерованных строк с разрывом строки между ними. Объясняют последовательность к воспроизведению дефекта")
    expected: str | None = Field(description="Ожидаемый результат. Формируется на основании требований или здравого смысла. Если ожидаемый результат не понятен - писать {должен заполнить тестировщик}")
    actual: str = Field(description="Фактический результат. Человекочитаемый результат, который объясняет что в ПО пошло не так")
    logs: str | None = Field(description="Логи баг-репорта. Необходимы разработчику для быстрого понимания и исправления. Могут отсутствовать")
    environment: Environment = Field(description="Описание среды, на которой обнаружен баг репорт.")
    priority: Priority = Field(description="Приоритет исправления баг-репорта. Формируется на основании влияния баг-репорта на работу ПО")


@dataclass
class Environment(BaseModel):
    side: str | None = Field(description="Место где обнаружен дефект. Ожидаем - дефект на фронте или на бэке")
    app_version: str | None = Field(description="Версия ПО на которой обнаружен дефект. Если не знаем - то <no info>")
    stand: Stand = Field(description="Стенд на котором обнаружен дефект")