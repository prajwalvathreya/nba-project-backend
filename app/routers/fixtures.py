from datetime import date, timedelta, time
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List
from app.models.fixture import FixtureResponse, FixtureWithUserPredictionResponse
from app.services.fixture_services import FixtureService
from app.database import DatabaseError
from app.models.prediction import PredictionResponse
from app.services.prediction_services import PredictionService
from app.auth import get_current_user
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


@router.get("/past", response_model=List[FixtureResponse])
async def get_fixtures_up_to_today():
    """
    Get all fixtures up to and including today.
    Returns all fixtures scheduled on or before today's date.
    """
    try:
        today = date.today()
        fixtures = FixtureService.get_fixtures_up_to_date(today)
        return fixtures
    except DatabaseError as e:
        logger.error(f"Failed to fetch fixtures up to today: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fixtures up to today"
        )


@router.get("/lastupdatedfixture", response_model=FixtureResponse)
async def get_last_updated_fixture():
    """
    Get the most recently updated fixture.
    Returns the fixture that was last modified in the database.
    """
    try:
        fixture = FixtureService.get_last_updated_fixture()
        if not fixture:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No fixtures found"
            )
        # Add game_date and game_time fields for response validation
        if 'start_time' in fixture and fixture['start_time']:
            fixture['game_date'] = fixture['start_time'].date()
            fixture['game_time'] = fixture['start_time'].time()
        else:
            fixture['game_date'] = None
            fixture['game_time'] = None
        return fixture
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Failed to fetch last updated fixture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch last updated fixture"
        )

@router.get("/next-fixtures-with-predictions", response_model=List[FixtureResponse])
async def get_next_fixtures_merged_with_predictions(current_user: dict = Depends(get_current_user)):
    """
    Get all fixtures for the next available game date, merging user's predictions (if any) into the fixture data.
    For fixtures with a prediction, use user's predicted scores for home_score and away_score. Otherwise, use fixture scores.
    """
    try:
        user_id = current_user["user_id"]
        fixtures = FixtureService.get_next_fixtures()
        predicted = PredictionService.get_next_fixtures_with_user_predictions(user_id)
        pred_map = {p["match_num"]: p for p in predicted}
        response = []
        for f in fixtures:
            pred = pred_map.get(f["match_num"])
            game_time = f.get("game_time")
            if isinstance(game_time, timedelta):
                total_seconds = int(game_time.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                game_time = time(hours, minutes, seconds)
            response.append({
                "match_num": f["match_num"],
                "home_team": f["home_team"],
                "away_team": f["away_team"],
                "home_score": pred.get("pred_home_score") if pred else f.get("home_score"),
                "away_score": pred.get("pred_away_score") if pred else f.get("away_score"),
                "completed": f["completed"],
                "start_time": f["start_time"],
                "game_date": f["game_date"],
                "game_time": game_time
            })
        return response
    except Exception as e:
        logger.error(f"Failed to fetch merged next fixtures with predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch merged fixtures with predictions"
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