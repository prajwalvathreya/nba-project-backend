from pydantic import BaseModel

class UserProfile(BaseModel):
    username: str
    bio: str | None = None

class UserStats(BaseModel):
    total_predictions: int
    correct_predictions: int
    exact_score_predictions: int

class BioUpdateRequest(BaseModel):
    bio: str