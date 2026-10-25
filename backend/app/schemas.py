from typing import Any

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    algorithm_id: str
    config: dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    execution_id: str
    algorithm_id: str
    status: str
    events: list[dict[str, Any]]
    final_state: dict[str, Any]
