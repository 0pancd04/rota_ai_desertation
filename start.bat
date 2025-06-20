@echo off
echo Starting AI Rota System...

REM Check if .venv exists, if not create it
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv
)

REM Install dependencies
echo Installing dependencies...
uv pip install -e .

REM Start the FastAPI server
echo Starting FastAPI server...
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 

pause