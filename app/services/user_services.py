from fastapi import HTTPException
from app.models.user_stats import UserProfile, UserStats
from typing import List, Dict, Any, Optional
from datetime import time, timedelta
from app.database import call_procedure
from app.database import DatabaseError
import logging

class UserService:
    """Service layer for user profile related operations"""

    @staticmethod
    def get_user_profile(cursor, user_id):
        cursor.execute("""
            SELECT u.username, p.bio
            FROM User u
            LEFT JOIN Profile p ON u.user_id = p.user_id
            WHERE u.user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return UserProfile(**result)

    @staticmethod
    def get_user_stats(cursor, user_id) -> UserStats:
        cursor.callproc("get_user_stats", [user_id])
        stats = cursor.fetchone()
        if not stats:
            raise HTTPException(status_code=404, detail="Stats not found")
        return UserStats(**stats)

    @staticmethod
    def update_user_bio(cursor, user_id, bio: str):
        # Upsert bio for user
        cursor.execute("""
            INSERT INTO Profile (user_id, bio)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE bio = VALUES(bio)
        """, (user_id, bio))
