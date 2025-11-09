#!/bin/bash
# Quick script to check Supabase data and export to CSV

python3 << 'EOF'
from supabase import create_client
import csv
from datetime import datetime

url = "https://zojouvfuvdgniqbmbegs.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc"

supabase = create_client(url, key)

# Get latest data
response = supabase.table('booking_data').select('*').order('id', desc=True).limit(20).execute()

print(f"\n{'='*80}")
print(f"SUPABASE DATA CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}\n")

if response.data:
    print(f"Latest {len(response.data)} records:\n")
    for i, record in enumerate(response.data, 1):
        print(f"{i}. ID: {record['id']}")
        print(f"   Date: {record['date']} | Time: {record['time']}")
        print(f"   Price: {record['price']} | Provider: {record['provider']}")
        print(f"   Created: {record.get('created_at', 'N/A')}")
        print()
else:
    print("No data found in Supabase\n")

# Total count
total = supabase.table('booking_data').select('id', count='exact').execute()
print(f"Total records in database: {total.count}")

# Export to CSV
if response.data:
    csv_file = f'supabase_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    # Get all data for export
    all_data = supabase.table('booking_data').select('*').execute()

    if all_data.data:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_data.data[0].keys())
            writer.writeheader()
            writer.writerows(all_data.data)
        print(f"\n✅ Exported to: {csv_file}")
        print(f"   Total records exported: {len(all_data.data)}")

print(f"\n{'='*80}\n")
EOF
