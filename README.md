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
│   │   ├── predictions.py
│   │   └── user.py
│   └── services/
│       ├── auth_services.py
│       ├── fixture_services.py
│       ├── group_services.py
│       ├── leaderboard_services.py
│       ├── prediction_services.py
│       └── user_services.py
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
- MySQL

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
DB_USER=root
DB_PASSWORD=Root@praj123
DB_NAME=nba_db
JWT_SECRET="x0otqii/nZd8GurNe9X8ly7cD1W/feARSjZJ0l/kyYZKOqrzT5NLRO7S6QgUB6bp
```


## Database Setup

1. **Start your MySQL server** and ensure you have a user with privileges to create databases, tables, triggers, and procedures.

2. **Configure your environment:**
      - Make sure your `.env` file (see above) is set up with the correct DB credentials (replace `your_actual_password_here` with your real password).

3. **Import the provided database dump (recommended):**
                  - If you have a `.sql` database dump file (e.g., `nba_db_dump.sql`), you can load all data, tables, triggers, and procedures in one step:
                        ```sh
                        mysql -u your_db_user -p nba_db < nba_db_dump.sql
                        ```
                  - This will set up everything, including all data and user stats, for the database named `nba_db`. **You do NOT need to run the backfill step if you use the dump.**

4. **(Alternative) Manual setup:**
      - If you want to set up from scratch, run:
        ```sh
        cd database-setup
        chmod +x setup_db.sh
        ./setup_db.sh
        ``

6. **Verify installation:**
      - Check that all tables exist: `SHOW TABLES;`
      - Check triggers: `SHOW TRIGGERS;`
      - Check stored procedures: `SHOW PROCEDURE STATUS WHERE Db = 'your_db_name';`

If you encounter errors, check your MySQL user permissions and that your `.env` file matches the DB setup.

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
- Thse is no need of running these scripts if the db dump is already provided.

## Troubleshooting
- If you get DB connection errors, check your `.env` and that MySQL is running.