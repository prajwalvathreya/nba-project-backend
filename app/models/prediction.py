from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date, time
from typing import Optional

class PredictionCreate(BaseModel):
    """Request model for creating a prediction"""
    group_id: int = Field(..., gt=0, description="Group ID")
    fixture_id: int = Field(..., gt=0, description="Fixture ID (match_num)")
    pred_home_score: int = Field(..., ge=0, description="Predicted home team score")
    pred_away_score: int = Field(..., ge=0, description="Predicted away team score")

class PredictionUpdate(BaseModel):
    """Request model for updating a prediction"""
    group_id: int = Field(..., gt=0, description="Group ID")
    fixture_id: int = Field(..., gt=0, description="Fixture ID (match_num)")
    pred_home_score: int = Field(..., ge=0, description="Updated home team score prediction")
    pred_away_score: int = Field(..., ge=0, description="Updated away team score prediction")

class PredictionQuery(BaseModel):
    """Query parameters for filtering predictions"""
    group_id: Optional[int] = Field(None, gt=0, description="Filter by group ID")

class PredictionResponse(BaseModel):
    """Response model for prediction details"""
    pid: int
    user_id: int
    group_id: int
    fixture_id: int
    pred_home_score: int
    pred_away_score: int
    prediction_time: datetime
    locked: bool
    points_earned: Optional[int] = None
    
    # Fixture details
    home_team: str
    away_team: str
    start_time: datetime
    completed: bool
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None
    game_date: date
    game_time: time
    
    model_config = ConfigDict(from_attributes=True)

class FixturePredictionResponse(BaseModel):
    """Response model for predictions on a specific fixture (for leaderboard view)"""
    pid: int
    user_id: int
    username: str
    pred_home_score: int
    pred_away_score: int
    prediction_time: datetime
    locked: bool
    points_earned: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class PredictionDeleteResponse(BaseModel):
    """Response model for deleting a prediction"""
    message: str
    deleted_count: int