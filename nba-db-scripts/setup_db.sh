#!/bin/bash

# Simple NBA Database Setup Script
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

# Check if database already exists
echo "Checking if database $DB_NAME exists..."
DB_EXISTS=$(mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD -e "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME='$DB_NAME';" --skip-column-names 2>/dev/null)

if [ "$DB_EXISTS" = "$DB_NAME" ]; then
    echo "Database $DB_NAME already exists."
    echo "Setup skipped - database and procedures are already in place."
    exit 0
fi

# Execute create-tables.sql (don't specify database - let script create it)
echo "Creating database and tables..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD < create-tables.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create database and tables"
    exit 1
fi

# Execute procedures.sql (now specify database since it exists)
echo "Creating procedures..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < procedures.sql

if [ $? -ne 0 ]; then
    echo "Error: Failed to create tables"
    exit 1
fi

echo "Database setup completed successfully!"