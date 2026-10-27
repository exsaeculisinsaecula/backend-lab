from typing import Any

from pydantic import BaseModel


class MessageOut(BaseModel):
    message: str
    detail: dict[str, Any] | None = None
