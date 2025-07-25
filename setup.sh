#!/bin/sh

pwd
ls

cd /app

echo "$(date +"%Y-%m-%d %H:%M:%S") | Installing dependencies..."
rm -rf .git
python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt
