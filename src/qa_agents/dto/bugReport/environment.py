from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Stand = Literal["dev", "st", "ift", "preprod", "prod", "unknown"]
Side = Literal["frontend", "backend"]

class Environment(BaseModel):
    """Среда, в которой обнаружен дефект. Заполняй только по тексту описания, ничего не выдумывай."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    side: Side | None = Field(
        description=(
            "Где виден дефект: frontend (интерфейс, экран, кнопка, вёрстка, вылет приложения) "
            "или backend (сервер, API, ответ сервиса, обработка данных, серверные логи). "
            "Если из текста не понять, верни null."
        ),
    )
    app_version: str | None = Field(
        description=(
            "Версия приложения или сервиса, скопированная из текста, например 5.13.1. "
            "Если версия не указана, верни строку <no info>."
        ),
        examples=["5.13.1", "<no info>"],
    )
    stand: Stand = Field(
        description=(
            "Стенд из текста: dev, st, ift, preprod или prod. Разговорные названия приводи к этим "
            "значениям («ифт» это ift, «прод» это prod, «препрод» это preprod). "
            "Если стенд не назван, верни unknown. Не угадывай."
        ),
    )
