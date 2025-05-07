#!/usr/bin/env python
"""
Script to update database schema for YCLIENTS parser business intelligence features.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import asyncpg
from config.settings import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# SQL for updating the schema
SCHEMA_UPDATE_SQL = """
-- Schema enhancement for YCLIENTS Parser
-- This script adds new fields to the booking_data table to store additional information

-- Add new columns to the booking_data table
ALTER TABLE booking_data 
ADD COLUMN IF NOT EXISTS location_name TEXT,
ADD COLUMN IF NOT EXISTS court_type TEXT,
ADD COLUMN IF NOT EXISTS time_category TEXT, -- e.g., "DAY", "EVENING", "WEEKEND"
ADD COLUMN IF NOT EXISTS duration INTEGER, -- in minutes
ADD COLUMN IF NOT EXISTS review_count INTEGER,
ADD COLUMN IF NOT EXISTS prepayment_required BOOLEAN DEFAULT FALSE;

-- Create index for more efficient querying
CREATE INDEX IF NOT EXISTS booking_data_court_type_idx ON booking_data(court_type);
CREATE INDEX IF NOT EXISTS booking_data_location_name_idx ON booking_data(location_name);
CREATE INDEX IF NOT EXISTS booking_data_time_category_idx ON booking_data(time_category);

-- Add new column to store raw venue data for future analysis
ALTER TABLE booking_data
ADD COLUMN IF NOT EXISTS raw_venue_data JSONB;

-- Create a new table for price history to track changes over time
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    booking_data_id INTEGER REFERENCES booking_data(id),
    price TEXT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(booking_data_id, recorded_at)
);

-- Create a new table for availability analytics
CREATE TABLE IF NOT EXISTS availability_analytics (
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id),
    date DATE NOT NULL,
    time_slot TEXT NOT NULL, -- e.g., "morning", "afternoon", "evening"
    available_count INTEGER DEFAULT 0,
    total_slots INTEGER DEFAULT 0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url_id, date, time_slot, recorded_at)
);
"""

async def update_schema():
    """Run the schema update SQL."""
    logger.info("Updating database schema for business intelligence features...")
    
    # Build connection string
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        # Connect to the database
        conn = await asyncpg.connect(connection_string)
        
        try:
            # Execute the schema update SQL
            await conn.execute(SCHEMA_UPDATE_SQL)
            logger.info("Database schema updated successfully!")
        finally:
            # Close the connection
            await conn.close()
    
    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        return False
    
    return True

def main():
    """Main function."""
    # Run the schema update
    success = asyncio.run(update_schema())
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())