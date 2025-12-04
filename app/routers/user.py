from fastapi import APIRouter, HTTPException, status, Depends
from app.services.user_services import UserService
from app.auth import get_current_user
from app.database import get_db_cursor
import logging
from app.models.user_stats import BioUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me/profile")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    try:
        with get_db_cursor() as cursor:
            profile = UserService.get_user_profile(cursor, current_user['user_id'])
            return profile
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to fetch profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch profile")

@router.put("/me/profile")
def update_my_bio(request: BioUpdateRequest, current_user: dict = Depends(get_current_user)):
    try:
        with get_db_cursor() as cursor:
            UserService.update_user_bio(cursor, current_user['user_id'], request.bio)
        return {"message": "Bio updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update bio: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update bio")

@router.get("/me/stats")
def get_my_stats(current_user: dict = Depends(get_current_user)):
    try:
        with get_db_cursor() as cursor:
            stats = UserService.get_user_stats(cursor, current_user['user_id'])
            return stats
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch stats")
