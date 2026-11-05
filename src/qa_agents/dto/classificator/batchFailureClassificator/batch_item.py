from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["product_bug", "flaky", "environment", "test_data"]


class BatchItem(BaseModel):
    id: str = Field(description="идентификатор падения")
    failure_text: str = Field(description="текст падения")
    category: Category = Field(description="категория падения")
    reasoning: str = Field(description="1-2 предложения: почему выбран этот класс")
