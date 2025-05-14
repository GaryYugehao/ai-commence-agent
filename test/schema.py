from pydantic import BaseModel
from typing import Optional, List, Dict

class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    image_url: str
    category: str
    tags: List[str]

class StartSessionPayload(BaseModel):
    user_info: Optional[Dict] = None

class StartSessionResponse(BaseModel):
    session_id: str
    initial_message: str

class ChatPayload(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    message: str

class TextRecommendQuery(BaseModel):
    query: str

class RecommendationResponse(BaseModel):
    recommendations: List[Product]
    message: Optional[str] = None

# class FileData(BaseModel):
#     data: str
#     mime_type: str