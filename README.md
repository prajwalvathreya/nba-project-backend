# Hoops Predictor Backend

A FastAPI backend for the Hoops Predictor app, where users compete to predict NBA game results, join groups, and climb leaderboards.

## Project Structure

```
nba-project-backend/
├── main.py
├── README.md
├── .env
├── .gitignore
├── app/
│   ├── auth.py
│   ├── database.py
│   ├── models/
│   │   ├── fixture.py
│   │   ├── group.py
│   │   ├── leaderboard.py
│   │   ├── prediction.py
│   │   └── user.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── fixtures.py
│   │   ├── groups.py
│   │   ├── leaderboard.py
│   │   └── predictions.py
│   └── services/
│       ├── auth_services.py
│       ├── fixture_services.py
│       ├── group_services.py
│       ├── leaderboard_services.py
│       └── prediction_services.py
├── database-setup/
│   ├── create_tables.sql
│   ├── fixture_procedures.sql
│   ├── functions.sql
│   ├── group_procedures.sql
│   ├── leaderboard_procedures.sql
│   ├── prediction_procedures.sql
│   ├── setup_db.sh
│   ├── triggers.sql
│   └── user_procedures.sql
├── scripts/
│   ├── download_fixtures.py
│   ├── insert_fixtures_into_db.py
│   └── nba_fixtures.json
└── test.py
```

## Tech Stack
- Python 3.10+
- FastAPI
- MySQL (or compatible, e.g. MariaDB)
- SQL (stored procedures)

## Environment Setup
1. **Clone the repo**
2. **Create a virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Environment Variables
Create a `.env` file in the root with your DB and secret settings. Example:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=hoops_predictor
SECRET_KEY=your_secret_key
```

## Database Setup
To set up the database schema, tables, triggers, and procedures, run:
```sh
cd database-setup
chmod +x setup_db.sh
./setup_db.sh
```
Make sure your MySQL server is running and accessible with the credentials in your `.env` file.

## Running the Backend
Start the FastAPI server:
```sh
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000` by default.

## API Documentation
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Scripts
- `scripts/download_fixtures.py`: Download NBA fixtures from an external API.
- `scripts/insert_fixtures_into_db.py`: Insert fixture data into the database.

## Troubleshooting
- If you get DB connection errors, check your `.env` and that MySQL is running.
- If migrations or setup fail, check user permissions and that the DB exists.