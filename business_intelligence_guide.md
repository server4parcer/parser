# Business Intelligence Features Guide

This guide describes how to use the new business intelligence features in the YCLIENTS Parser project. These features enable comprehensive market analysis for sports facility businesses.

## Setup Instructions

### 1. Update Database Schema

First, run the database schema update script to add new tables and columns required for business intelligence:

```bash
python scripts/update_db_schema.py
```

This script will:
- Add new columns to the booking_data table (court_type, time_category, duration, etc.)
- Create price_history table for tracking price changes
- Create availability_analytics table for analyzing court availability
- Create appropriate indexes for performance

### 2. Restart the Application

After updating the schema, restart the application:

```bash
# If using Docker
docker-compose down
docker-compose up -d

# If running manually
python src/main.py
```

## Using the Business Intelligence Features

### Accessing Analytics via API

The application provides several new API endpoints for business intelligence:

#### 1. Price Analytics

```
GET /analytics/pricing
```

Parameters:
- `court_type`: Filter by court type (TENNIS, BASKETBALL, etc.)
- `time_category`: Filter by time category (DAY, EVENING, WEEKEND)
- `location`: Filter by location name
- `time_frame`: Time period to analyze (last_7_days, last_30_days, last_90_days)

Example:
```
GET /analytics/pricing?court_type=TENNIS&time_category=EVENING
```

Response includes:
- Price ranges by court type (min, max, avg)
- Price comparison by time categories

#### 2. Availability Analytics

```
GET /analytics/availability
```

Parameters:
- `court_type`: Filter by court type
- `location`: Filter by location name
- `time_frame`: Time period to analyze

Example:
```
GET /analytics/availability?location=central&court_type=BASKETBALL
```

Response includes:
- Availability by location and date
- Court types by venue

#### 3. Price History Analytics

```
GET /analytics/price_history
```

Parameters:
- `venue_id`: Filter by venue ID
- `court_type`: Filter by court type
- `start_date`: Beginning date for analysis (YYYY-MM-DD)
- `days`: Number of days to analyze (default: 30)

Example:
```
GET /analytics/price_history?court_type=TENNIS&days=60
```

Response includes:
- Historical price changes
- Current vs. historical pricing

### Filtering Booking Data

You can now filter booking data using the new business intelligence fields:

```
GET /data?court_type=TENNIS&time_category=WEEKEND&location_name=central
```

Available filters:
- `court_type`: Type of court (TENNIS, BASKETBALL, SQUASH, etc.)
- `time_category`: Time of day category (DAY, EVENING, WEEKEND)
- `location_name`: Location name

### Enhanced Data Export

The export functionality now supports business intelligence fields:

```
GET /export?format=json&court_type=TENNIS&include_analytics=true
```

Parameters:
- Standard parameters: format, url_id, url, date_from, date_to
- New parameters:
  - `location_name`: Filter by location
  - `court_type`: Filter by court type
  - `time_category`: Filter by time category
  - `include_analytics`: Include analytics data in export

## Business Intelligence Fields

The new business intelligence features add the following fields to booking data:

- **court_type**: Type of court/facility (TENNIS, BASKETBALL, FOOTBALL, VOLLEYBALL, SQUASH, BADMINTON, OTHER)
- **time_category**: Time category (DAY, EVENING, WEEKEND)
- **duration**: Duration in minutes
- **location_name**: Venue location name
- **review_count**: Number of reviews for the venue
- **prepayment_required**: Whether prepayment is required (true/false)
- **raw_venue_data**: Raw data about the venue

## Example Use Cases

### Price Comparison across Venues

To compare prices across different venues for tennis courts in the evening:

```
GET /analytics/pricing?court_type=TENNIS&time_category=EVENING
```

### Identify High-Demand Time Slots

To identify which time slots have the highest demand:

```
GET /analytics/availability
```

### Track Price Changes

To track how prices have changed over time for specific court types:

```
GET /analytics/price_history?court_type=BASKETBALL&days=90
```

### Export Data for External Analysis

To export data for analysis in Excel or other tools:

```
GET /export?format=csv&court_type=TENNIS&time_category=WEEKEND&include_analytics=true
```

## Programmatic Usage Examples

### Python Example: Price Analysis

```python
import requests

api_url = "http://localhost:8000"
headers = {"X-API-Key": "your-api-key"}

# Get price analytics for tennis courts
response = requests.get(
    f"{api_url}/analytics/pricing",
    params={"court_type": "TENNIS"},
    headers=headers
)

data = response.json()["data"]

# Print average prices by time category
for item in data["price_comparison"]:
    print(f"{item['court_type']} - {item['time_category']}: {item['avg_price']} RUB")
```

### Python Example: Export Data with Filters

```python
import requests

api_url = "http://localhost:8000"
headers = {"X-API-Key": "your-api-key"}

# Export data for tennis courts on weekends
response = requests.get(
    f"{api_url}/export",
    params={
        "format": "json",
        "court_type": "TENNIS",
        "time_category": "WEEKEND",
        "include_analytics": "true"
    },
    headers=headers
)

# Get the download URL
download_url = response.json()["data"]["url"]

# Download the file
file_response = requests.get(f"{api_url}{download_url}", headers=headers)

with open("tennis_weekend_data.json", "wb") as f:
    f.write(file_response.content)
```

## Troubleshooting

### Common Issues

1. **Missing columns in database**: Run the update_db_schema.py script to add new columns.
2. **No court type data**: The system needs to parse new data after the update to detect court types.
3. **Incomplete location data**: Manual location tagging might be needed for some venues.

### Data Quality

For best results:
- Allow the system to parse data for at least 7 days
- Tag venues with accurate location information
- Verify court type detection results and manually correct if needed

For further assistance, contact the development team.