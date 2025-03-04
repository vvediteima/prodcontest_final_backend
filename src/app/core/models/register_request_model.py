from pydantic import BaseModel
from typing import Optional, List

class RegisterRequestModel(BaseModel):
    login: str
    name: str
    surname: str
    password: str
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    job: Optional[str] = None
    company: Optional[str] = None