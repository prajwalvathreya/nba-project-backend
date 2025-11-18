from typing import List, Dict, Any, Optional
from app.database import call_procedure
from app.database import DatabaseError
import logging

logger = logging.getLogger(__name__)

class LeaderboardService:
    """Service layer for leaderboard and scoring operations"""
    
    @staticmethod
    def get_group_leaderboard(group_id: int) -> List[Dict[str, Any]]:
        """
        Get leaderboard rankings for a group.
        
        Args:
            group_id: The group ID
            
        Returns:
            List[Dict]: Leaderboard entries sorted by rank
        """
        try:
            result = call_procedure('get_group_leaderboard', [group_id])
            
            if not result:
                logger.info(f"No leaderboard entries found for group {group_id}")
                return []
            
            logger.info(f"Retrieved leaderboard for group {group_id}: {len(result)} entries")
            return result
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch group leaderboard: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching group leaderboard: {e}")
            raise DatabaseError(f"Failed to fetch group leaderboard: {str(e)}")
    
    @staticmethod
    def get_user_rank_in_group(user_id: int, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's rank and stats in a specific group.
        
        Args:
            user_id: The user ID
            group_id: The group ID
            
        Returns:
            Dict: User's rank info or None if not found
        """
        try:
            result = call_procedure('get_user_rank_in_group', [user_id, group_id])
            
            if not result:
                logger.info(f"User {user_id} not found in group {group_id}")
                return None
            
            logger.info(f"Retrieved rank for user {user_id} in group {group_id}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch user rank: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user rank: {e}")
            raise DatabaseError(f"Failed to fetch user rank: {str(e)}")
    
    @staticmethod
    def complete_fixture(fixture_id: int, home_score: int, away_score: int) -> Dict[str, Any]:
        """
        Complete a fixture and trigger automatic scoring (admin only).
        
        Args:
            fixture_id: The fixture ID
            home_score: Final home team score
            away_score: Final away team score
            
        Returns:
            Dict: Completed fixture data
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            result = call_procedure('complete_fixture', [fixture_id, home_score, away_score])
            
            if not result:
                raise DatabaseError("Failed to complete fixture")
            
            logger.info(f"Fixture {fixture_id} completed: {home_score}-{away_score}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to complete fixture: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error completing fixture: {e}")
            raise DatabaseError(f"Failed to complete fixture: {str(e)}")
    
    @staticmethod
    def update_fixture_scores(fixture_id: int, home_score: int, away_score: int) -> Dict[str, Any]:
        """
        Update scores for an already-completed fixture (admin only).
        
        Args:
            fixture_id: The fixture ID
            home_score: Corrected home team score
            away_score: Corrected away team score
            
        Returns:
            Dict: Updated fixture data
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            result = call_procedure('update_fixture_scores', [fixture_id, home_score, away_score])
            
            if not result:
                raise DatabaseError("Failed to update fixture scores")
            
            logger.info(f"Fixture {fixture_id} scores updated: {home_score}-{away_score}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to update fixture scores: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating fixture scores: {e}")
            raise DatabaseError(f"Failed to update fixture scores: {str(e)}")
    
    @staticmethod
    def recalculate_all_leaderboards() -> Dict[str, Any]:
        """
        Recalculate all leaderboards (utility function for maintenance).
        
        Returns:
            Dict: Recalculation statistics
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            result = call_procedure('recalculate_all_leaderboards', [])
            
            if not result:
                raise DatabaseError("Failed to recalculate leaderboards")
            
            logger.info(f"All leaderboards recalculated: {result[0]}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to recalculate leaderboards: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error recalculating leaderboards: {e}")
            raise DatabaseError(f"Failed to recalculate leaderboards: {str(e)}")