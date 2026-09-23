from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any


class PredictionResult(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    model: Optional[str] = None
    probability: Optional[float] = None
    prediction: Optional[Any] = None
    class_name: Optional[str] = Field(default=None, serialization_alias="class")
    inference_time: float = 0.0

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)
