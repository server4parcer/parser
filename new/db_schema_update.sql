-- Schema enhancement for YCLIENTS Parser
-- This script adds new fields to the booking_data table to store additional information

-- Add new columns to the booking_data table
ALTER TABLE booking_data 
ADD COLUMN location_name TEXT,
ADD COLUMN court_type TEXT,
ADD COLUMN time_category TEXT, -- e.g., "DAY", "EVENING", "WEEKEND"
ADD COLUMN duration INTEGER, -- in minutes
ADD COLUMN review_count INTEGER,
ADD COLUMN prepayment_required BOOLEAN DEFAULT FALSE;

-- Create index for more efficient querying
CREATE INDEX IF NOT EXISTS booking_data_court_type_idx ON booking_data(court_type);
CREATE INDEX IF NOT EXISTS booking_data_location_name_idx ON booking_data(location_name);
CREATE INDEX IF NOT EXISTS booking_data_time_category_idx ON booking_data(time_category);

-- Add new column to store raw venue data for future analysis
ALTER TABLE booking_data
ADD COLUMN raw_venue_data JSONB;

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
