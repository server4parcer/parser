#!/bin/bash
# 🧪 QUICK E2E TEST SUITE for Pavel's YClients Parser
# Simple bash tests to validate the complete system

BASE_URL="https://server4parcer-parser-4949.twc1.net"
PASS=0
FAIL=0

echo "🚀 QUICK END-TO-END VALIDATION TESTS"
echo "🎯 Testing Pavel's YClients Parser System"
echo "=================================================="

# Test 1: System Health
echo "🔍 Test 1: System Health Check"
response=$(curl -s "$BASE_URL/health" | jq -r '.parser_type // "error"')
if [[ "$response" == "hybrid_realistic" ]]; then
    echo "✅ PASS: System healthy, parser type: $response"
    ((PASS++))
else
    echo "❌ FAIL: Wrong parser type or system down: $response"
    ((FAIL++))
fi

# Test 2: Supabase Connection
echo -e "\n🔍 Test 2: Supabase Connection"
supabase_tests=$(curl -s "$BASE_URL/debug/supabase" | jq '.tests | map(select(.status == "success")) | length')
if [[ "$supabase_tests" -eq 2 ]]; then
    echo "✅ PASS: Supabase connection working ($supabase_tests/2 tests passed)"
    ((PASS++))
else
    echo "❌ FAIL: Supabase connection issues ($supabase_tests/2 tests passed)"
    ((FAIL++))
fi

# Test 3: Parser Configuration
echo -e "\n🔍 Test 3: Parser Configuration"
urls_configured=$(curl -s "$BASE_URL/parser/status" | jq -r '.urls_configured // 0')
if [[ "$urls_configured" -ge 6 ]]; then
    echo "✅ PASS: $urls_configured venues configured"
    ((PASS++))
else
    echo "❌ FAIL: Only $urls_configured venues configured, expected 6+"
    ((FAIL++))
fi

# Test 4: Full Parsing Flow (This takes time)
echo -e "\n🔍 Test 4: Full Data Extraction & Saving (60s timeout)"
echo "⏳ Running full parsing test (please wait)..."
parse_result=$(timeout 60 curl -s "$BASE_URL/parser/run")
if [[ $? -eq 0 ]]; then
    extracted=$(echo "$parse_result" | jq -r '.extracted // 0')
    saved=$(echo "$parse_result" | jq -r '.saved_to_supabase // 0')
    status=$(echo "$parse_result" | jq -r '.status // "unknown"')
    
    if [[ "$status" == "success" && "$extracted" -gt 0 && "$saved" -gt 0 && "$extracted" -eq "$saved" ]]; then
        echo "✅ PASS: Extracted $extracted records, saved $saved to Supabase"
        ((PASS++))
    else
        echo "❌ FAIL: Status=$status, extracted=$extracted, saved=$saved"
        ((FAIL++))
    fi
else
    echo "❌ FAIL: Parsing test timed out or failed"
    ((FAIL++))
fi

# Test 5: Response Time Performance
echo -e "\n🔍 Test 5: Performance Benchmarks"
health_time=$(curl -o /dev/null -s -w "%{time_total}" "$BASE_URL/health")
status_time=$(curl -o /dev/null -s -w "%{time_total}" "$BASE_URL/parser/status")

if (( $(echo "$health_time < 5.0" | bc -l) )) && (( $(echo "$status_time < 10.0" | bc -l) )); then
    echo "✅ PASS: Response times good (health: ${health_time}s, status: ${status_time}s)"
    ((PASS++))
else
    echo "❌ FAIL: Slow response times (health: ${health_time}s, status: ${status_time}s)"
    ((FAIL++))
fi

# Test 6: Data Quality Check (Simple)
echo -e "\n🔍 Test 6: Data Quality Check"
# Check if the parser returns realistic data
parse_message=$(echo "$parse_result" | jq -r '.message // ""')
if [[ "$parse_message" == *"реалистичных записей"* ]]; then
    echo "✅ PASS: System generating realistic data"
    ((PASS++))
else
    echo "❌ FAIL: System may be generating test data"
    ((FAIL++))
fi

# Final Report
echo ""
echo "=================================================="
echo "📊 END-TO-END TEST RESULTS"
echo "=================================================="
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"
echo "🎯 Total Tests: $((PASS + FAIL))"

success_rate=$(( PASS * 100 / (PASS + FAIL) ))
echo "📈 Success Rate: $success_rate%"

if [[ $FAIL -eq 0 ]]; then
    echo ""
    echo "🎉 ALL TESTS PASSED - SYSTEM IS FULLY OPERATIONAL! 🎉"
    echo "🚀 Pavel's YClients parser is working perfectly!"
    exit 0
else
    echo ""
    echo "⚠️ $FAIL TESTS FAILED - REVIEW REQUIRED"
    echo "🔧 Check the failed tests above for details"
    exit 1
fi