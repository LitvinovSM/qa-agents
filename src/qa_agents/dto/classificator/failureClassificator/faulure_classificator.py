from pydantic import BaseModel, Field

from qa_agents.dto.classificator.batchFailureClassificator.batch_item import Category


class FailureClassification(BaseModel):
    """Ответ модели о падении: из него же строится JSON Schema для Ollama.

    Порядок полей важен: модель пишет JSON сверху вниз, значит сначала рассуждает, потом решает.
    """

    reasoning: str = Field(description="1-2 предложения: почему выбран этот класс")
    evidence: str = Field(description="Точная цитата из текста падения, на которой основан вывод")
    category: Category
    confidence: float = Field(ge=0.0, le=1.0, description="Уверенность от 0 до 1")
