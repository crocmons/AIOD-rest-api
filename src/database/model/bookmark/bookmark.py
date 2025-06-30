from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class BookmarkBase(SQLModel):
    user_identifier: str  
    resource_identifier: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class Bookmark(BookmarkBase, table=True): # type: ignore [call-arg]
    id: Optional[int] = Field(default=None, primary_key=True)
    __tablename__ = "bookmark"
    
