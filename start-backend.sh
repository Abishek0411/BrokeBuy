#!/bin/bash

# Simple backend startup script
cd /home/abishek/Downloads/proj_BrokeBuy_backend

# Activate virtual environment and start backend
source myenv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# Save PID
echo $! > .backend.pid
echo "Backend started with PID: $!"
