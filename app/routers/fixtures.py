from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from app.models.fixture import FixtureResponse
from app.services.fixture_services import FixtureService
from app.database import DatabaseError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("/next", response_model=List[FixtureResponse])
async def get_next_fixtures():
    """
    Get all fixtures for the next available game date.
    
    Returns all games scheduled for the earliest date from today onwards.
    If today has games, returns today's games. Otherwise, returns the next date with games.
    """
    try:
        fixtures = FixtureService.get_next_fixtures()
        return fixtures
        
    except DatabaseError as e:
        logger.error(f"Failed to fetch next fixtures: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fixtures"
        )


@router.get("/upcoming", response_model=List[FixtureResponse])
async def get_upcoming_fixtures(
    days: int = Query(7, ge=1, le=30, description="Number of days ahead (1-30)")
):
    """
    Get all fixtures for the next N days.
    
    Parameters:
    - **days**: Number of days to look ahead (default: 7, min: 1, max: 30)
    
    Returns all games scheduled within the specified number of days from today.
    """
    try:
        fixtures = FixtureService.get_upcoming_fixtures(days)
        return fixtures
        
    except DatabaseError as e:
        logger.error(f"Failed to fetch upcoming fixtures: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fixtures"
        )


@router.get("/{match_num}", response_model=FixtureResponse)
async def get_fixture(match_num: int):
    """
    Get a specific fixture by match number.
    
    Parameters:
    - **match_num**: The unique match number
    
    Returns the complete details of a single fixture.
    """
    try:
        fixture = FixtureService.get_fixture_by_id(match_num)
        
        if not fixture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fixture with match number {match_num} not found"
            )
        
        return fixture
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Failed to fetch fixture {match_num}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fixture"
        )