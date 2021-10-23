from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from .users import PyObjectId
class BaseToDoModel(BaseModel):
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
                "tag":"Infosys",
                "name":"Homework 1",
                "deadline": "YYYY-MM-DD"
            }

class ToDoModel(BaseToDoModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name:str
    deadline: date
    tag: str
 
class DeleteToDoModel(BaseToDoModel):
    name: Optional[str]
    deadline: Optional[date]
    tag: Optional[str]


