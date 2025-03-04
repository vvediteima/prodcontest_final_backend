from pydantic import BaseModel
from typing import Optional, List

class LoginRequestModel(BaseModel):
    login: str
    password: str