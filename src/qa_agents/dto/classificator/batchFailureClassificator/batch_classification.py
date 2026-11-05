from pydantic import BaseModel, Field

from qa_agents.dto.classificator.batchFailureClassificator.batch_item import BatchItem


class BatchClassification(BaseModel):
    items: list[BatchItem] = Field(description="Список с падениями, по которым произведена классификация")
