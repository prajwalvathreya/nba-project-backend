#!/bin/bash

# NBA Database Setup Script
# Reads database credentials from environment variables

# Database name - set as variable in script
DB_NAME="nba_db"

# Check if required environment variables are set
if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "Error: Please set the following environment variables:"
    echo "  DB_USER - MySQL username"
    echo "  DB_PASSWORD - MySQL password"
    echo ""
    echo "Example:"
    echo "  export DB_USER=root"
    echo "  export DB_PASSWORD=mypassword"
    exit 1
fi

# Optional: DB_HOST defaults to localhost if not set
DB_HOST=${DB_HOST:-localhost}

echo "Setting up NBA Database..."
echo "Host: $DB_HOST"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Check if database already exists
echo "Checking database status..."
DB_EXISTS=$(mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='$DB_NAME';" --skip-column-names 2>/dev/null)

if [ "$DB_EXISTS" = "$DB_NAME" ]; then
    echo "Database $DB_NAME already exists - will update procedures and triggers"
else
    echo "Database $DB_NAME does not exist - will create everything"
fi
echo ""

# Execute create_tables.sql (includes CREATE DATABASE IF NOT EXISTS)
echo "Creating/verifying database and tables..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD < create_tables.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create database and tables"
    exit 1
fi

# Execute functions.sql
echo "Creating/updating functions..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < functions.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create functions"
    exit 1
fi

# Execute triggers.sql
echo "Creating/updating triggers..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < triggers.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create triggers"
    exit 1
fi

# Execute user_procedures.sql
echo "Creating/updating user procedures..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < user_procedures.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create user procedures"
    exit 1
fi

# Execute fixture_procedures.sql
echo "Creating/updating fixture procedures..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < fixture_procedures.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create fixture procedures"
    exit 1
fi

# Execute group_procedures.sql
echo "Creating/updating group procedures..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < group_procedures.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create group procedures"
    exit 1
fi

# Execute prediction_procedures.sql
echo "Creating/updating prediction procedures..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < prediction_procedures.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create prediction procedures"
    exit 1
fi

# Execute leaderboard_procedures.sql
echo "Creating/updating leaderboard procedures..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < leaderboard_procedures.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create leaderboard procedures"
    exit 1
fi

echo ""
echo "=========================================="
echo "Database setup completed successfully!"
echo "=========================================="
if [ "$DB_EXISTS" = "$DB_NAME" ]; then
    echo "  Updated Database: $DB_NAME"
else
    echo "  Created Database: $DB_NAME"
fi
echo "  Created Tables"
echo "  Created Functions"
echo "  Created Procedures"
echo "  Created Triggers"
echo "=========================================="