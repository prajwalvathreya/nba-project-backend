from fastapi import APIRouter, HTTPException, status, Depends, Path
from typing import List
from app.models.leaderboard import (
    LeaderboardEntry,
    UserRankResponse,
    FixtureComplete,
    FixtureScoreUpdate,
    FixtureCompleteResponse,
    LeaderboardRecalculateResponse
)
from app.services.leaderboard_services import LeaderboardService
from app.auth import get_current_user
from app.database import DatabaseError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/{group_id}", response_model=List[LeaderboardEntry])
async def get_group_leaderboard(
    group_id: int = Path(..., gt=0, description="Group ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get leaderboard rankings for a group.
    
    - **group_id**: The group's unique identifier
    
    Returns all users in the group sorted by rank (highest points first).
    Includes stats like total predictions, exact predictions, and average points.
    """
    try:
        leaderboard = LeaderboardService.get_group_leaderboard(group_id)
        
        if not leaderboard:
            # Empty leaderboard is valid (group exists but no scores yet)
            return []
        
        return leaderboard
        
    except DatabaseError as e:
        logger.error(f"Failed to fetch leaderboard for group {group_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaderboard"
        )


@router.get("/{group_id}/me", response_model=UserRankResponse)
async def get_my_rank(
    group_id: int = Path(..., gt=0, description="Group ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get your rank and stats in a specific group.
    
    - **group_id**: The group's unique identifier
    
    Returns your current rank, total points, predictions made, and comparison to other players.
    """
    try:
        rank_info = LeaderboardService.get_user_rank_in_group(
            user_id=current_user['user_id'],
            group_id=group_id
        )
        
        if not rank_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"You are not a member of group {group_id}"
            )
        
        return rank_info
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Failed to fetch user rank: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your rank"
        )


# ============================================================================
# ADMIN ENDPOINTS (Fixture Management)
# ============================================================================

@router.post("/admin/fixtures/{fixture_id}/complete", response_model=FixtureCompleteResponse)
async def complete_fixture(
    fixture_id: int = Path(..., gt=0, description="Fixture ID"),
    scores: FixtureComplete = ...,
    current_user: dict = Depends(get_current_user)
):
    """
    Complete a fixture and trigger automatic scoring (ADMIN ONLY).
    
    - **fixture_id**: The fixture's unique identifier
    - **home_score**: Final home team score
    - **away_score**: Final away team score
    
    This endpoint:
    1. Marks the fixture as completed
    2. Automatically calculates points for all predictions
    3. Updates all affected group leaderboards
    4. Recalculates rankings
    
    Note: This is an admin-only operation. In production, add proper admin authorization.
    """
    try:
        completed_fixture = LeaderboardService.complete_fixture(
            fixture_id=fixture_id,
            home_score=scores.home_score,
            away_score=scores.away_score
        )
        
        logger.info(
            f"Admin {current_user['username']} completed fixture {fixture_id}: "
            f"{scores.home_score}-{scores.away_score}"
        )
        return completed_fixture
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fixture not found"
            )
        elif "already completed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fixture is already completed. Use update endpoint to correct scores."
            )
        else:
            logger.error(f"Failed to complete fixture: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete fixture"
            )


@router.put("/admin/fixtures/{fixture_id}/scores", response_model=FixtureCompleteResponse)
async def update_fixture_scores(
    fixture_id: int = Path(..., gt=0, description="Fixture ID"),
    scores: FixtureScoreUpdate = ...,
    current_user: dict = Depends(get_current_user)
):
    """
    Update scores for an already-completed fixture (ADMIN ONLY).
    
    - **fixture_id**: The fixture's unique identifier
    - **home_score**: Corrected home team score
    - **away_score**: Corrected away team score
    
    Use this endpoint to correct scores after initial completion.
    This will:
    1. Update the fixture scores
    2. Recalculate points for all predictions
    3. Update all affected group leaderboards
    4. Recalculate rankings
    
    Note: This is an admin-only operation. In production, add proper admin authorization.
    """
    try:
        updated_fixture = LeaderboardService.update_fixture_scores(
            fixture_id=fixture_id,
            home_score=scores.home_score,
            away_score=scores.away_score
        )
        
        logger.info(
            f"Admin {current_user['username']} updated fixture {fixture_id} scores: "
            f"{scores.home_score}-{scores.away_score}"
        )
        return updated_fixture
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fixture not found"
            )
        elif "not completed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fixture is not completed yet. Use complete endpoint instead."
            )
        elif "same as current" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New scores are the same as current scores"
            )
        else:
            logger.error(f"Failed to update fixture scores: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update fixture scores"
            )


@router.post("/admin/recalculate", response_model=LeaderboardRecalculateResponse)
async def recalculate_all_leaderboards(
    current_user: dict = Depends(get_current_user)
):
    """
    Recalculate all leaderboards (ADMIN ONLY - Utility/Maintenance).
    
    This endpoint recalculates:
    - Total points for all users in all groups
    - Rankings for all groups
    
    Use this for:
    - Fixing inconsistencies
    - Maintenance after database changes
    - Recovery from errors
    
    Note: This is an admin-only operation. In production, add proper admin authorization.
    """
    try:
        stats = LeaderboardService.recalculate_all_leaderboards()
        
        logger.info(
            f"Admin {current_user['username']} triggered full leaderboard recalculation: "
            f"{stats['groups_updated']} groups, {stats['users_updated']} users"
        )
        return stats
        
    except DatabaseError as e:
        logger.error(f"Failed to recalculate leaderboards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recalculate leaderboards"
        )