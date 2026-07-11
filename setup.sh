#!/bin/bash
# VPS setup script — run once after cloning
set -e

echo "=== Agentic AI News Bot Setup ==="

cd "$(dirname "$0")"

echo "1. Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "2. Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "3. Creating .env from example..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Edit .env and fill in your Gmail credentials:"
    echo "    nano $(pwd)/.env"
else
    echo "   .env already exists — skipping"
fi

echo ""
echo "4. To test the bot manually:"
echo "   source venv/bin/activate && python aggregator.py"
echo ""
echo "5. To schedule daily at 7 AM UTC, add this to crontab (crontab -e):"
BOT_DIR="$(pwd)"
echo "   0 7 * * * $BOT_DIR/venv/bin/python $BOT_DIR/aggregator.py >> $BOT_DIR/cron.log 2>&1"
echo ""
echo "=== Setup complete ==="
