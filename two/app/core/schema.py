from pydantic import BaseModel

class BaseRespone(BaseModel):
    message: str = "Data retrieved successfully"
    status: str = "success"