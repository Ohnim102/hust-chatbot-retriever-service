from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class OllamaRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    chat_id: Optional[int] = None
    options: Optional[Dict[str, float]] = Field(default_factory=dict)
    streaming: Optional[bool] = Field(default=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.options is None:
            self.options = {}
        self.options.setdefault('temperature', 0.7)
        self.options.setdefault('top_p', 0.9)
