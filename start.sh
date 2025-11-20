#!/bin/bash

# Start Backend
echo "Starting Backend..."
# Start Backend
echo "Starting Backend..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
./venv/bin/python -m uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend..."
cd web
npm run dev &
FRONTEND_PID=$!

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
