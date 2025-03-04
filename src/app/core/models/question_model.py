from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class QuestionModel(BaseModel):
    id: Optional[UUID] = None  # добавлено поле id
    title: str
    description: str
    tags: List[str]

    owner_id: Optional[UUID] = None
    owner_name: Optional[str] = None
    owner_surname: Optional[str] = None
    owner_login: Optional[str] = None

    class Config:
        from_attributes = True