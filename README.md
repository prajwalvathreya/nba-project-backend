# NBA Scores Prediction Website

## Project Structure

```
nba_project-backend/
├── app/                           # Main application directory
│   ├── models/                         # Database models
│   ├── routers/                        # Route handlers
│   └── services/                       # Business logic functions
├── database-setup/                # Database setup and management
│   ├── create-tables.sql               # Database schema
│   ├── procedures.sql                  # Stored procedures
│   └── setup_db.sh                     # Database setup script
├── scripts/                       # Utility scripts
│   ├── download_fixtures.py            # Using NBA api to download current season fixtures
│   ├── import_fixtures_into_db.py      # NBA fixtures import script
│   └── nba_fixtures.json               # JSON containing NBA fixture information from API call
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```