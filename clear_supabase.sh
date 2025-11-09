#!/bin/bash
# Clear all data from Supabase booking_data table

echo "Clearing all data from Supabase booking_data table..."
echo ""

python3 << 'PYTHON'
from supabase import create_client

url = "https://zojouvfuvdgniqbmbegs.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc"

supabase = create_client(url, key)

# Get count before
before = supabase.table('booking_data').select('id', count='exact').execute()
print(f"Records before: {before.count}")

# Delete all
result = supabase.table('booking_data').delete().neq('id', 0).execute()
print(f"✅ Deleted records")

# Verify
after = supabase.table('booking_data').select('id', count='exact').execute()
print(f"Records after: {after.count}")
print("")
if after.count == 0:
    print("✅ Table is now empty - ready for test")
else:
    print(f"⚠️  Warning: {after.count} records remain")
PYTHON
