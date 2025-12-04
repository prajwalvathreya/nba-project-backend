
import pymysql
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env at project root
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'nba_db'),
}

def get_all_users(cursor):
    cursor.execute("SELECT user_id FROM User")
    return [row[0] for row in cursor.fetchall()]

def get_all_groups(cursor):
    cursor.execute("SELECT group_id FROM `Group`")
    return [row[0] for row in cursor.fetchall()]

def get_completed_fixtures(cursor):
    cursor.execute("SELECT match_num FROM Fixture WHERE completed = 1")
    return [row[0] for row in cursor.fetchall()]

def set_fixture_completed(cursor, fixture_id, completed):
    cursor.execute("UPDATE Fixture SET completed = %s WHERE match_num = %s", (completed, fixture_id))

def insert_prediction(cursor, user_id, group_id, fixture_id):
    pred_home = random.randint(80, 130)
    pred_away = random.randint(80, 130)
    try:
        cursor.execute(
            """
            INSERT INTO Prediction (user_id, group_id, fixture_id, pred_home_score, pred_away_score)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE pred_home_score=VALUES(pred_home_score), pred_away_score=VALUES(pred_away_score)
            """,
            (user_id, group_id, fixture_id, pred_home, pred_away)
        )
    except Exception as e:
        print(f"Failed to insert prediction for user {user_id}, group {group_id}, fixture {fixture_id}: {e}")

def main():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    users = get_all_users(cursor)
    groups = get_all_groups(cursor)
    fixtures = get_completed_fixtures(cursor)
    print(f"Users: {users}\nGroups: {groups}\nFixtures: {fixtures}")
    # Set all completed fixtures to not completed
    for fixture_id in fixtures:
        set_fixture_completed(cursor, fixture_id, 0)
    conn.commit()
    # Insert predictions
    for user_id in users:
        for group_id in groups:
            for fixture_id in fixtures:
                insert_prediction(cursor, user_id, group_id, fixture_id)
    conn.commit()
    # Set all fixtures back to completed
    for fixture_id in fixtures:
        set_fixture_completed(cursor, fixture_id, 1)
    conn.commit()
    cursor.close()
    conn.close()
    print("Random predictions inserted for all users, groups, and completed fixtures (temporarily unlocked).")

if __name__ == "__main__":
    main()
