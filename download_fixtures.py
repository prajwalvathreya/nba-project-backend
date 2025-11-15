import requests
import json
from datetime import datetime

def download_nba_fixtures(output_file="nba_fixtures_2025_26.json"):
    url = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    fixtures = []
    fix_count = 1

    # Filter: games on or after 21 October 2025 (excluding preseason games)
    season_start_date = datetime(2025, 10, 21)

    for day in data["leagueSchedule"]["gameDates"]:
        for game in day.get("games", []):
            time_est = game.get("gameDateTimeEst")
            if not time_est:
                continue

            # Parse start_time as datetime
            try:
                game_datetime = datetime.strptime(time_est[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                continue

            # Skip games before season start
            if game_datetime < season_start_date:
                continue

            fixtures.append({
                "fixture_number": fix_count,
                "home_team": {
                    "city": game["homeTeam"]["teamCity"],
                    "name": game["homeTeam"]["teamName"],
                    "tricode": game["homeTeam"]["teamTricode"]
                },
                "away_team": {
                    "city": game["awayTeam"]["teamCity"],
                    "name": game["awayTeam"]["teamName"],
                    "tricode": game["awayTeam"]["teamTricode"]
                },
                "start_time": time_est,
                "home_score": None,
                "away_score": None,
                "completed": False
            })
            fix_count += 1

    # write to json file
    with open(output_file, "w") as f:
        json.dump(fixtures, f, indent=2)

    print(f"Saved {len(fixtures)} fixtures starting from 21 Oct to {output_file}")


if __name__ == "__main__":
    download_nba_fixtures()
