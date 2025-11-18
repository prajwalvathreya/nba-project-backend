from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class FixtureComplete(BaseModel):
    """Request model for completing a fixture (admin only)"""
    home_score: int
    away_score: int

class FixtureScoreUpdate(BaseModel):
    """Request model for updating fixture scores (admin only)"""
    home_score: int
    away_score: int

class LeaderboardEntry(BaseModel):
    """Response model for a single leaderboard entry"""
    user_id: int
    username: str
    email: str
    total_points: int
    rank_position: Optional[int] = None
    last_updated: datetime
    total_predictions: int
    scored_predictions: int
    exact_predictions: int
    avg_points_per_prediction: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserRankResponse(BaseModel):
    """Response model for user's rank in a group"""
    user_id: int
    username: str
    total_points: int
    rank_position: Optional[int] = None
    last_updated: datetime
    total_predictions: int
    scored_predictions: int
    exact_predictions: int
    avg_points_per_prediction: Optional[float] = None
    total_players: int
    
    model_config = ConfigDict(from_attributes=True)

class FixtureCompleteResponse(BaseModel):
    """Response model after completing a fixture"""
    match_num: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    completed: bool
    start_time: datetime
    total_predictions: int
    predictions_scored: int
    
    model_config = ConfigDict(from_attributes=True)

class LeaderboardRecalculateResponse(BaseModel):
    """Response model for leaderboard recalculation"""
    groups_updated: int
    users_updated: int
    total_points_awarded: int