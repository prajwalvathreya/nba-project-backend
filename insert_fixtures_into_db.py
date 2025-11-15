import json
import pymysql
from datetime import datetime
import sys
import os

class NBAFixtureImporter:
    def __init__(self, db_config):
        """Initialize with database configuration"""
        self.db_config = db_config
        self.connection = None
    
    def connect_db(self):
        """Connect to MySQL database"""
        try:
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            print("Connected to database successfully!")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def load_json_file(self, file_path):
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            print(f"Loaded {len(data)} fixtures from {file_path}")
            return data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {e}")
            return None
        except Exception as e:
            print(f"Error loading file: {e}")
            return None
    
    def format_team_name(self, team_data):
        """Format team name from JSON data"""
        # Using City + Name format (most descriptive)
        return f"{team_data['city']} {team_data['name']}"
    
    def convert_datetime(self, iso_datetime):
        """Convert ISO datetime string to MySQL datetime format"""
        try:
            # Parse ISO format: "2025-10-21T19:30:00Z"
            dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
            # Convert to MySQL datetime format
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error converting datetime {iso_datetime}: {e}")
            return None
    
    def clear_existing_fixtures(self, season='2025-26'):
        """Clear existing fixtures using stored procedure"""
        try:
            cursor = self.connection.cursor()
            cursor.callproc('clear_season_fixtures', [season])
            
            # Get the result (deleted count)
            result = cursor.fetchone()
            deleted_count = result['deleted_count'] if result else 0
            
            cursor.close()
            print(f"Cleared {deleted_count} existing fixtures for {season} season")
            return True
        except Exception as e:
            print(f"Error clearing fixtures: {e}")
            return False
    
    def insert_fixtures(self, fixtures_data, clear_existing=False):
        """Insert fixtures using stored procedure"""
        if not self.connection:
            print("No database connection!")
            return False
        
        # Optional: Clear existing fixtures
        if clear_existing:
            if not self.clear_existing_fixtures():
                return False
        
        successful_inserts = 0
        failed_inserts = 0
        
        try:
            for i, fixture in enumerate(fixtures_data, 1):
                try:
                    # Format the data
                    home_team = self.format_team_name(fixture['home_team'])
                    away_team = self.format_team_name(fixture['away_team'])
                    start_time = self.convert_datetime(fixture['start_time'])
                    home_score = fixture['home_score']
                    away_score = fixture['away_score']
                    completed = fixture['completed']
                    api_game_id = fixture['fixture_number']
                    season = '2025-26'
                    
                    # Skip if datetime conversion failed
                    if start_time is None:
                        print(f"Skipping fixture {i}: Invalid datetime")
                        failed_inserts += 1
                        continue
                    
                    # Call stored procedure to insert fixture
                    cursor = self.connection.cursor()
                    cursor.callproc('insert_fixture', [
                        home_team,
                        away_team,
                        start_time,
                        home_score,
                        away_score,
                        completed,
                        api_game_id,
                        season
                    ])
                    cursor.close()
                    
                    successful_inserts += 1
                    
                    # Progress indicator
                    if i % 100 == 0:
                        print(f"Processed {i}/{len(fixtures_data)} fixtures...")
                        
                except Exception as e:
                    print(f"Error inserting fixture {i}: {e}")
                    failed_inserts += 1
                    continue
            
            print(f"\nImport Summary:")
            print(f"Successfully inserted: {successful_inserts} fixtures")
            print(f"Failed insertions: {failed_inserts}")
            print(f"Total processed: {len(fixtures_data)}")
            
            return successful_inserts > 0
            
        except Exception as e:
            print(f"Database error during bulk insert: {e}")
            return False
    
    def verify_import(self, season='2025-26'):
        """Verify the import using stored procedure"""
        try:
            cursor = self.connection.cursor()
            
            # Use stored procedure to get season statistics
            cursor.callproc('get_season_stats', [season])
            stats = cursor.fetchone()
            cursor.close()
            
            # Get sample fixtures
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT home_team, away_team, start_time, completed 
                FROM Fixture 
                WHERE season = %s 
                ORDER BY start_time 
                LIMIT 5
            """, [season])
            sample_fixtures = cursor.fetchall()
            cursor.close()
            
            print(f"\nImport Verification for {season} season:")
            print(f"Total fixtures in database: {stats['total_fixtures']}")
            print(f"Completed games: {stats['completed_games']}")
            print(f"Upcoming games: {stats['upcoming_games']}")
            print(f"Season runs from: {stats['first_game']} to {stats['last_game']}")
            
            print(f"\nSample fixtures:")
            for fixture in sample_fixtures:
                status = "COMPLETED" if fixture['completed'] else "UPCOMING"
                print(f"{status}: {fixture['home_team']} vs {fixture['away_team']} - {fixture['start_time']}")
            
        except Exception as e:
            print(f"Error verifying import: {e}")


def main():
    """Main function to run the import"""
    
    # Get database configuration from environment variables
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': 'nba_db'  # Hardcoded name
    }
    
    # Check if required environment variables are set
    if not db_config['user'] or not db_config['password']:
        print("Error: Please set the following environment variables:")
        print("  DB_USER - MySQL username")
        print("  DB_PASSWORD - MySQL password")
        print("  DB_HOST - MySQL host (optional, defaults to localhost)")
        print()
        print("Example:")
        print("  export DB_USER=root")
        print("  export DB_PASSWORD=mypassword")
        sys.exit(1)

    json_file_path = 'nba_fixtures.json'  # Path to JSON file

    print(f"Using JSON file: {json_file_path}")
    print(f"Database: {db_config['database']} on {db_config['host']}")
    print(f"User: {db_config['user']}")
    
    # Create importer instance
    importer = NBAFixtureImporter(db_config)
    
    try:
        # Connect to database
        if not importer.connect_db():
            sys.exit(1)
        
        # Load JSON data
        fixtures_data = importer.load_json_file(json_file_path)
        if not fixtures_data:
            sys.exit(1)
        
        # Import fixtures
        print(f"\nStarting import of {len(fixtures_data)} fixtures...")
        
        # Ask user if they want to clear existing data
        clear_existing = input("\nClear existing fixtures for 2025-26 season? (y/N): ").lower().strip() == 'y'
        
        success = importer.insert_fixtures(fixtures_data, clear_existing=clear_existing)
        
        if success:
            # Verify the import
            importer.verify_import()
            print(f"\nImport completed successfully!")
        else:
            print(f"\nImport failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\nImport cancelled by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        importer.close_connection()

if __name__ == "__main__":
    main()