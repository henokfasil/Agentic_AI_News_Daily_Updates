#!/bin/bash
# check_cron.sh — Verify cron timing and help debug email delays

echo "=== Agentic AI Bot — Cron Timing Check ==="
echo ""

# Check if cron job exists
echo "📋 Current cron job:"
crontab -l 2>/dev/null | grep -E "aggregator|agentic_ai" | head -1

if ! crontab -l 2>/dev/null | grep -q "aggregator\|agentic_ai"; then
    echo "   ❌ No cron job found! Run: crontab -e and add:"
    echo "   TZ=Europe/Paris"
    echo "   0 22 * * * /root/agentic_ai_bot/venv/bin/python /root/agentic_ai_bot/aggregator.py >> /root/agentic_ai_bot/cron.log 2>&1"
    exit 1
fi

echo ""
echo "📅 Last 5 executions (from cron.log):"
if [ -f "cron.log" ]; then
    tail -5 cron.log | grep "Starting aggregation"
    echo ""
    echo "✅ Cron is running!"
else
    echo "   ⚠️  No cron.log found yet"
fi

echo ""
echo "🕒 System timezone:"
date +"%Z (UTC%z)"

echo ""
echo "📊 To see full cron logs:"
echo "   tail -50 cron.log | less"

echo ""
echo "🔧 To change cron time, edit:"
echo "   crontab -e"
echo "   (Change '0 22' for a different hour)"
