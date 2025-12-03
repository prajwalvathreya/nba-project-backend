from typing import List, Dict, Any, Optional
from datetime import time, timedelta
from app.database import call_procedure
from app.database import DatabaseError
import logging

logger = logging.getLogger(__name__)

class PredictionService:
    """Service layer for prediction-related operations"""
    
    @staticmethod
    def _convert_timedelta_to_time(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert timedelta objects to time objects for game_time field.
        
        Args:
            data: List of prediction dictionaries
            
        Returns:
            List of prediction dictionaries with converted game_time
        """
        for prediction in data:
            if 'game_time' in prediction and isinstance(prediction['game_time'], timedelta):
                total_seconds = int(prediction['game_time'].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                prediction['game_time'] = time(hours, minutes, seconds)
        return data
    
    @staticmethod
    def create_prediction(
        user_id: int,
        group_id: int,
        fixture_id: int,
        pred_home_score: int,
        pred_away_score: int
    ) -> Dict[str, Any]:
        """
        Create a new prediction.
        
        Args:
            user_id: User making the prediction
            group_id: Group the prediction is for
            fixture_id: Fixture being predicted
            pred_home_score: Predicted home team score
            pred_away_score: Predicted away team score
            
        Returns:
            Dict: Created prediction data
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('create_prediction', [
                user_id, group_id, fixture_id, pred_home_score, pred_away_score
            ])
            
            if not result:
                raise DatabaseError("Failed to create prediction")
            
            # Convert timedelta to time
            result = PredictionService._convert_timedelta_to_time(result)
            
            logger.info(f"Prediction created: user={user_id}, group={group_id}, fixture={fixture_id}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to create prediction: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating prediction: {e}")
            raise DatabaseError(f"Failed to create prediction: {str(e)}")
    
    @staticmethod
    def get_user_predictions(user_id: int, group_id: int) -> List[Dict[str, Any]]:
        """
        Get all predictions for a user in a specific group.
        
        Args:
            user_id: The user ID
            group_id: The group ID
        
        Returns:
            List[Dict]: List of user's predictions in the group
        """
        try:
            result = call_procedure('get_user_predictions', [user_id, group_id])
            if not result:
                logger.info(f"No predictions found for user {user_id} in group {group_id}")
                return []
            result = PredictionService._convert_timedelta_to_time(result)
            logger.info(f"Found {len(result)} predictions for user {user_id} in group {group_id}")
            return result
        except DatabaseError as e:
            logger.error(f"Failed to fetch user predictions: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user predictions: {e}")
            raise DatabaseError(f"Failed to fetch user predictions: {str(e)}")

    @staticmethod
    def get_user_predictions_by_match_range(user_id: int, min_match_num: Optional[int] = None, max_match_num: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get only the latest prediction per fixture for a user within a specific match number range.
        """
        try:
            result = call_procedure('get_user_predictions_by_match_range', [user_id, min_match_num, max_match_num])
            if not result:
                logger.info(f"No predictions found for user {user_id} in match range {min_match_num}-{max_match_num}")
                return []
            result = PredictionService._convert_timedelta_to_time(result)
            # Group by fixture_id and keep only the latest prediction (by prediction_time)
            latest_preds = {}
            for pred in result:
                fid = pred['fixture_id']
                if fid not in latest_preds or pred['prediction_time'] > latest_preds[fid]['prediction_time']:
                    latest_preds[fid] = pred
            logger.info(f"Filtered to {len(latest_preds)} latest predictions for user {user_id} in match range {min_match_num}-{max_match_num}")
            return list(latest_preds.values())
        except DatabaseError as e:
            logger.error(f"Failed to fetch user predictions by match range: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user predictions by match range: {e}")
            raise DatabaseError(f"Failed to fetch user predictions by match range: {str(e)}")
    
    @staticmethod
    def get_all_user_predictions(user_id: int) -> List[Dict[str, Any]]:
        """
        Get all predictions for a user across all groups.
        
        Args:
            user_id: The user ID
            
        Returns:
            List[Dict]: List of all user's predictions
        """
        try:
            result = call_procedure('get_all_user_predictions', [user_id])
            
            if not result:
                logger.info(f"No predictions found for user {user_id}")
                return []
            
            # Convert timedelta to time
            result = PredictionService._convert_timedelta_to_time(result)
            
            logger.info(f"Found {len(result)} total predictions for user {user_id}")
            return result
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch all user predictions: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching all user predictions: {e}")
            raise DatabaseError(f"Failed to fetch all user predictions: {str(e)}")
    
    @staticmethod
    def get_fixture_predictions(fixture_id: int, group_id: int) -> List[Dict[str, Any]]:
        """
        Get all predictions for a specific fixture in a group.
        
        Args:
            fixture_id: The fixture ID
            group_id: The group ID
            
        Returns:
            List[Dict]: List of predictions for the fixture
        """
        try:
            result = call_procedure('get_fixture_predictions', [fixture_id, group_id])
            
            if not result:
                logger.info(f"No predictions found for fixture {fixture_id} in group {group_id}")
                return []
            
            logger.info(f"Found {len(result)} predictions for fixture {fixture_id} in group {group_id}")
            return result
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch fixture predictions: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching fixture predictions: {e}")
            raise DatabaseError(f"Failed to fetch fixture predictions: {str(e)}")
    
    @staticmethod
    def get_prediction_by_id(pid: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific prediction by ID.
        
        Args:
            pid: The prediction ID
            
        Returns:
            Dict: Prediction data or None if not found
        """
        try:
            result = call_procedure('get_prediction_by_id', [pid])
            
            if not result:
                logger.info(f"Prediction {pid} not found")
                return None
            
            # Convert timedelta to time
            result = PredictionService._convert_timedelta_to_time(result)
            
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch prediction {pid}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching prediction {pid}: {e}")
            raise DatabaseError(f"Failed to fetch prediction: {str(e)}")
    
    @staticmethod
    def update_prediction(
        user_id: int,
        group_id: int,
        fixture_id: int,
        pred_home_score: int,
        pred_away_score: int
    ) -> Dict[str, Any]:
        """
        Update an existing prediction.
        
        Args:
            user_id: User updating the prediction
            group_id: Group the prediction is in
            fixture_id: Fixture being predicted
            pred_home_score: Updated home team score prediction
            pred_away_score: Updated away team score prediction
            
        Returns:
            Dict: Updated prediction data
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('update_prediction', [
                user_id, group_id, fixture_id, pred_home_score, pred_away_score
            ])
            
            if not result:
                raise DatabaseError("Failed to update prediction")
            
            # Convert timedelta to time
            result = PredictionService._convert_timedelta_to_time(result)
            
            logger.info(f"Prediction updated: user={user_id}, group={group_id}, fixture={fixture_id}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to update prediction: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating prediction: {e}")
            raise DatabaseError(f"Failed to update prediction: {str(e)}")
    
    @staticmethod
    def delete_prediction(user_id: int, group_id: int, fixture_id: int) -> int:
        """
        Delete a prediction.
        
        Args:
            user_id: User deleting the prediction
            group_id: Group the prediction is in
            fixture_id: Fixture being predicted
            
        Returns:
            int: Number of rows deleted (should be 1)
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('delete_prediction', [user_id, group_id, fixture_id])
            
            if not result:
                raise DatabaseError("Failed to delete prediction")
            
            deleted_count = result[0]['deleted_count']
            logger.info(f"Prediction deleted: user={user_id}, group={group_id}, fixture={fixture_id}")
            return deleted_count
            
        except DatabaseError as e:
            logger.error(f"Failed to delete prediction: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting prediction: {e}")
            raise DatabaseError(f"Failed to delete prediction: {str(e)}")
    
    @staticmethod
    def get_next_fixtures_with_user_predictions(user_id: int) -> List[Dict[str, Any]]:
        """
        Get all fixtures for the next available game date, with the user's prediction (if any) for each fixture.
        Calls the new stored procedure with a LEFT JOIN.
        """
        try:
            result = call_procedure('get_next_fixtures_with_user_predictions', [user_id])
            # Optionally convert timedelta fields, if needed
            # Optionally post-process to match response model
            return result if result else []
        except Exception as e:
            logger.error(f"Failed to fetch next fixtures with user predictions: {e}")
            return []
