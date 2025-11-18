from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models.prediction import (
    PredictionCreate,
    PredictionUpdate,
    PredictionResponse,
    FixturePredictionResponse,
    PredictionDeleteResponse
)
from app.services.prediction_services import PredictionService
from app.auth import get_current_user
from app.database import DatabaseError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    prediction_data: PredictionCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new prediction for a fixture in a group.
    
    - **group_id**: The group this prediction is for
    - **fixture_id**: The fixture (game) being predicted
    - **pred_home_score**: Predicted score for home team
    - **pred_away_score**: Predicted score for away team
    
    Rules:
    - Cannot predict after game has started
    - Can only have one prediction per fixture per group
    - Prediction will be locked when game starts
    """
    try:
        prediction = PredictionService.create_prediction(
            user_id=current_user['user_id'],
            group_id=prediction_data.group_id,
            fixture_id=prediction_data.fixture_id,
            pred_home_score=prediction_data.pred_home_score,
            pred_away_score=prediction_data.pred_away_score
        )
        
        logger.info(f"Prediction created by {current_user['username']} for fixture {prediction_data.fixture_id}")
        return prediction
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors from stored procedure
        if "game has already started" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot predict - game has already started"
            )
        elif "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a prediction for this game in this group"
            )
        else:
            logger.error(f"Failed to create prediction: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create prediction"
            )


@router.get("/me", response_model=List[PredictionResponse])
async def get_my_predictions(
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all predictions for the current user.
    
    - **group_id** (optional): Filter predictions by specific group
    
    If group_id is provided, returns predictions for that group only.
    If not provided, returns all predictions across all groups.
    """
    try:
        if group_id:
            predictions = PredictionService.get_user_predictions(
                user_id=current_user['user_id'],
                group_id=group_id
            )
        else:
            predictions = PredictionService.get_all_user_predictions(
                user_id=current_user['user_id']
            )
        
        return predictions
        
    except DatabaseError as e:
        logger.error(f"Failed to fetch user predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your predictions"
        )


@router.get("/fixture/{fixture_id}", response_model=List[FixturePredictionResponse])
async def get_fixture_predictions(
    fixture_id: int,
    group_id: int = Query(..., description="Group ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all predictions for a specific fixture in a group.
    
    - **fixture_id**: The fixture (game) to get predictions for
    - **group_id**: The group to get predictions from
    
    Shows all users' predictions for this game in the specified group.
    Useful for seeing how others predicted and comparing scores.
    """
    try:
        predictions = PredictionService.get_fixture_predictions(
            fixture_id=fixture_id,
            group_id=group_id
        )
        
        return predictions
        
    except DatabaseError as e:
        logger.error(f"Failed to fetch fixture predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fixture predictions"
        )


@router.get("/{pid}", response_model=PredictionResponse)
async def get_prediction(
    pid: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific prediction by ID.
    
    - **pid**: The prediction ID
    
    Returns full prediction details including fixture info and actual scores if game completed.
    """
    try:
        prediction = PredictionService.get_prediction_by_id(pid)
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediction {pid} not found"
            )
        
        return prediction
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Failed to fetch prediction {pid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch prediction"
        )


@router.put("", response_model=PredictionResponse)
async def update_prediction(
    prediction_data: PredictionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing prediction.
    
    - **group_id**: The group the prediction is in
    - **fixture_id**: The fixture being predicted
    - **pred_home_score**: New predicted score for home team
    - **pred_away_score**: New predicted score for away team
    
    Rules:
    - Can only update before game starts
    - Cannot update locked predictions
    - Can only update your own predictions
    """
    try:
        prediction = PredictionService.update_prediction(
            user_id=current_user['user_id'],
            group_id=prediction_data.group_id,
            fixture_id=prediction_data.fixture_id,
            pred_home_score=prediction_data.pred_home_score,
            pred_away_score=prediction_data.pred_away_score
        )
        
        logger.info(f"Prediction updated by {current_user['username']} for fixture {prediction_data.fixture_id}")
        return prediction
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found for this game in this group"
            )
        elif "locked" in error_msg or "already started" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update - prediction is locked or game has started"
            )
        else:
            logger.error(f"Failed to update prediction: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update prediction"
            )


@router.delete("", response_model=PredictionDeleteResponse)
async def delete_prediction(
    group_id: int = Query(..., description="Group ID"),
    fixture_id: int = Query(..., description="Fixture ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a prediction.
    
    - **group_id**: The group the prediction is in
    - **fixture_id**: The fixture being predicted
    
    Rules:
    - Can only delete before game starts
    - Cannot delete locked predictions
    - Can only delete your own predictions
    """
    try:
        deleted_count = PredictionService.delete_prediction(
            user_id=current_user['user_id'],
            group_id=group_id,
            fixture_id=fixture_id
        )
        
        logger.info(f"Prediction deleted by {current_user['username']} for fixture {fixture_id}")
        return {
            "message": "Prediction successfully deleted",
            "deleted_count": deleted_count
        }
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found for this game in this group"
            )
        elif "locked" in error_msg or "already started" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete - prediction is locked or game has started"
            )
        else:
            logger.error(f"Failed to delete prediction: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete prediction"
            )