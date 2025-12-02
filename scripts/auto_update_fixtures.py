import requests
import os
import random


BACKEND_BASE_URL = "http://localhost:8000/leaderboard/admin/fixtures"
BACKEND_LOGIN_URL = "http://localhost:8000/auth/login"
ADMIN_ID = os.getenv("DB_ADMIN_ID")
ADMIN_PASSWORD = os.getenv("DB_ADMIN_PASS")

def get_admin_token():
    """
    Logs in as admin and retrieves JWT token using credentials from environment variables.
    """
    if not ADMIN_ID or not ADMIN_PASSWORD:
        raise ValueError("DB_ADMIN_ID and DB_ADMIN_PASS must be set in environment variables.")
    data = {"username": ADMIN_ID, "password": ADMIN_PASSWORD}
    response = requests.post(BACKEND_LOGIN_URL, json=data)
    if response.status_code != 200:
        raise Exception(f"Failed to log in as admin: {response.status_code} {response.text}")
    token = response.json().get("access_token")
    if not token:
        raise Exception("No access_token found in login response.")
    return token

def generate_random_fixture_scores(fixture_ids):
    """
    Generates random home and away scores for a list of fixture IDs.
    Returns a list of dicts: [{"fixture_id": int, "home_score": int, "away_score": int}, ...]
    """
    fixtures = []
    for fid in fixture_ids:
        home_score = random.randint(80, 130)
        away_score = random.randint(80, 130)
        fixtures.append({
            "fixture_id": fid,
            "home_score": home_score,
            "away_score": away_score
        })
    return fixtures

def update_fixture_score(fixture, admin_token):
    """
    Calls the backend's upsert fixture scores endpoint:
    PUT /leaderboard/admin/fixtures/{fixture_id}/scores
    Body: {"home_score": int, "away_score": int}
    Headers: Authorization: Bearer <ADMIN_TOKEN>
    """
    url = f"{BACKEND_BASE_URL}/{fixture['fixture_id']}/scores"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    data = {
        "home_score": fixture["home_score"],
        "away_score": fixture["away_score"]
    }
    response = requests.put(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Updated fixture {fixture['fixture_id']}: {fixture['home_score']}-{fixture['away_score']}")
    else:
        print(f"Failed to update fixture {fixture['fixture_id']}: {response.status_code} {response.text}")

def fetch_fixture_ids_till_today(admin_token):
    """
    Fetches all fixture IDs from the backend up to today using /fixtures/past.
    """
    url = "http://localhost:8000/fixtures/past"
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    fixtures = response.json()
    return [f["match_num"] for f in fixtures]

def main():
    admin_token = get_admin_token()
    fixture_ids = fetch_fixture_ids_till_today(admin_token)
    fixtures = generate_random_fixture_scores(fixture_ids)
    for fixture in fixtures:
        update_fixture_score(fixture, admin_token)

if __name__ == "__main__":
    main()
