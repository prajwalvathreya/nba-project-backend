from typing import List, Dict, Any, Optional
from datetime import time, timedelta
from app.database import call_procedure, DatabaseError
import logging

logger = logging.getLogger(__name__)

class FixtureService:
    """Service layer for fixture-related operations"""
    
    @staticmethod
    def _convert_timedelta_to_time(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert timedelta objects to time objects for game_time field.
        
        Args:
            data: List of fixture dictionaries
            
        Returns:
            List of fixture dictionaries with converted game_time
        """
        for fixture in data:
            if 'game_time' in fixture and isinstance(fixture['game_time'], timedelta):
                # Convert timedelta to time
                total_seconds = int(fixture['game_time'].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                fixture['game_time'] = time(hours, minutes, seconds)
        return data
    
    @staticmethod
    def get_next_fixtures() -> List[Dict[str, Any]]:
        """
        Get all fixtures for the next available game date.
        
        Returns:
            List[Dict]: List of fixtures for the next game date
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('get_next_fixtures', [])
            
            if not result:
                logger.info("No fixtures found for next game date")
                return []
            
            # Convert timedelta to time
            result = FixtureService._convert_timedelta_to_time(result)
            
            game_date = result[0]['game_date'] if result else None
            logger.info(f"Found {len(result)} fixtures for {game_date}")
            return result
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch next fixtures: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching next fixtures: {e}")
            raise DatabaseError(f"Failed to fetch next fixtures: {str(e)}")
    
    @staticmethod
    def get_upcoming_fixtures(days: int = 7) -> List[Dict[str, Any]]:
        """
        Get all fixtures for the next N days.
        
        Args:
            days: Number of days ahead to fetch fixtures for (default: 7)
            
        Returns:
            List[Dict]: List of upcoming fixtures
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('get_upcoming_fixtures', [days])
            
            if not result:
                logger.info(f"No fixtures found for next {days} days")
                return []
            
            # Convert timedelta to time
            result = FixtureService._convert_timedelta_to_time(result)
            
            logger.info(f"Found {len(result)} fixtures for next {days} days")
            return result
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch upcoming fixtures: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching upcoming fixtures: {e}")
            raise DatabaseError(f"Failed to fetch upcoming fixtures: {str(e)}")
    
    @staticmethod
    def get_fixture_by_id(match_num: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific fixture by match number.
        
        Args:
            match_num: The match number to fetch
            
        Returns:
            Dict: Fixture data or None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('get_fixture_by_id', [match_num])
            
            if not result:
                logger.info(f"Fixture {match_num} not found")
                return None
            
            # Convert timedelta to time
            result = FixtureService._convert_timedelta_to_time(result)
            
            logger.info(f"Found fixture {match_num}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch fixture {match_num}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching fixture {match_num}: {e}")
            raise DatabaseError(f"Failed to fetch fixture {match_num}: {str(e)}")
    
    @staticmethod
    def get_fixtures_up_to_date(to_date) -> List[Dict[str, Any]]:
        """
        Get all fixtures scheduled on or before the given date.
        Args:
            to_date: date object (YYYY-MM-DD)
        Returns:
            List[Dict]: List of fixtures
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('get_fixtures_up_to_date', [to_date])
            if not result:
                logger.info(f"No fixtures found up to {to_date}")
                return []
            # Add game_date and game_time fields from start_time for Pydantic compatibility
            for fixture in result:
                if 'start_time' in fixture and fixture['start_time']:
                    fixture['game_date'] = fixture['start_time'].date()
                    fixture['game_time'] = fixture['start_time'].time()
                else:
                    fixture['game_date'] = None
                    fixture['game_time'] = None
            result = FixtureService._convert_timedelta_to_time(result)
            logger.info(f"Found {len(result)} fixtures up to {to_date}")
            return result
        except DatabaseError as e:
            logger.error(f"Failed to fetch fixtures up to {to_date}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching fixtures up to {to_date}: {e}")
            raise DatabaseError(f"Failed to fetch fixtures up to {to_date}: {str(e)}")