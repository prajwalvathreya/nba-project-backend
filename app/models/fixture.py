from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional

class FixtureResponse(BaseModel):
    """Response model for a single fixture"""
    match_num: int
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    completed: bool
    start_time: datetime
    game_date: date
    game_time: time
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        }