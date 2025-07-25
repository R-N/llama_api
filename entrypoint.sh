#!/bin/sh

echo "$(date +"%Y-%m-%d %H:%M:%S") | Syncing mounted source to /app..."
find /app -mindepth 1 -maxdepth 1 ! -name 'venv' ! -name 'models' ! -name 'assets' -exec rm -rf {} +
rsync -av --exclude=venv --exclude=.git /mnt/src/ /app/
rm -rf .git

cd /app

echo "$(date +"%Y-%m-%d %H:%M:%S") | Installing dependencies..."
python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

echo "$(date +"%Y-%m-%d %H:%M:%S") | Starting bot..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
