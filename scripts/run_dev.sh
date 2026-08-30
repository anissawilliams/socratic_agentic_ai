#!/bin/bash

# Resolve project root based on this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project root: $PROJECT_ROOT"

# Activate virtual environment
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
else
    echo "Warning: .venv not found at $PROJECT_ROOT/.venv"
fi

cleanup() {
    echo ""
    echo "Stopping development environment..."

    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi

    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null
    fi
}

trap cleanup EXIT INT TERM

echo "Starting FastAPI backend..."

(
    cd "$PROJECT_ROOT" || exit 1
    python -m uvicorn app.main:app \
        --reload \
        --reload-dir "$PROJECT_ROOT/app"
) &

BACKEND_PID=$!

echo "Starting React frontend..."

(
    cd "$PROJECT_ROOT/frontend" || exit 1
    npm run dev
) &

FRONTEND_PID=$!

echo ""
echo "Development environment is running."
echo "Backend:  http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Frontend URL will be printed by Vite."
echo ""
echo "Press Ctrl+C to stop everything."

wait