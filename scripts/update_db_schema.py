#!/usr/bin/env python
"""
Database schema update script for YClients Parser
Adds new tables and columns required for business intelligence features
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db_manager import DatabaseManager
from config.logging_config import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# SQL statements for schema updates
SCHEMA_UPDATES = """
-- Add new columns to booking_data table
ALTER TABLE IF EXISTS booking_data 
ADD COLUMN IF NOT EXISTS court_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS time_category VARCHAR(10),
ADD COLUMN IF NOT EXISTS duration INTEGER,
ADD COLUMN IF NOT EXISTS address VARCHAR(255),
ADD COLUMN IF NOT EXISTS city VARCHAR(100),
ADD COLUMN IF NOT EXISTS region VARCHAR(100),
ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS prepayment_required BOOLEAN DEFAULT FALSE;

-- Create price_history table
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    venue_name VARCHAR(255) NOT NULL,
    court_type VARCHAR(20),
    time_category VARCHAR(10),
    price NUMERIC(10, 2) NOT NULL,
    recorded_date DATE NOT NULL,
    recorded_time TIME NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    CONSTRAINT fk_venue_id
        FOREIGN KEY(venue_id)
        REFERENCES booking_data(venue_id)
        ON DELETE CASCADE
);

-- Create availability_analytics table
CREATE TABLE IF NOT EXISTS availability_analytics (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    venue_name VARCHAR(255) NOT NULL,
    court_type VARCHAR(20),
    date DATE NOT NULL,
    time_slot TIME NOT NULL,
    time_category VARCHAR(10),
    is_available BOOLEAN NOT NULL,
    check_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_venue_id
        FOREIGN KEY(venue_id)
        REFERENCES booking_data(venue_id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_booking_data_court_type ON booking_data(court_type);
CREATE INDEX IF NOT EXISTS idx_booking_data_time_category ON booking_data(time_category);
CREATE INDEX IF NOT EXISTS idx_booking_data_city ON booking_data(city);
CREATE INDEX IF NOT EXISTS idx_price_history_venue_id ON price_history(venue_id);
CREATE INDEX IF NOT EXISTS idx_price_history_court_type ON price_history(court_type);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded_date ON price_history(recorded_date);
CREATE INDEX IF NOT EXISTS idx_availability_analytics_venue_id ON availability_analytics(venue_id);
CREATE INDEX IF NOT EXISTS idx_availability_analytics_date ON availability_analytics(date);
CREATE INDEX IF NOT EXISTS idx_availability_analytics_court_type ON availability_analytics(court_type);
"""

def update_schema(force=False):
    """
    Updates the database schema with new tables and columns
    
    Args:
        force (bool): If True, forces update even if some operations might fail
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        logger.info("Starting database schema update for business intelligence features")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        connection = db_manager.get_connection()
        
        if not connection:
            logger.error("Failed to connect to database")
            return False
        
        # Execute schema updates
        cursor = connection.cursor()
        
        try:
            # Split and execute each statement separately
            for statement in SCHEMA_UPDATES.split(';'):
                if statement.strip():
                    logger.info(f"Executing: {statement.strip()}")
                    cursor.execute(statement)
            
            # Commit the transaction
            connection.commit()
            logger.info("Schema update completed successfully")
            
        except Exception as e:
            # Roll back in case of error
            connection.rollback()
            logger.error(f"Error updating schema: {str(e)}")
            
            if not force:
                return False
            
        finally:
            # Close cursor and connection
            cursor.close()
            db_manager.close_connection()
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error during schema update: {str(e)}")
        return False

def main():
    """
    Main function to run schema update
    """
    parser = argparse.ArgumentParser(description='Update database schema for YClients Parser')
    parser.add_argument('--force', action='store_true', help='Force update even if some operations might fail')
    args = parser.parse_args()
    
    success = update_schema(args.force)
    
    if success:
        print("Database schema updated successfully!")
        sys.exit(0)
    else:
        print("Failed to update database schema. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()